"""Protocol v2 validation and offline high-speed analysis; no serial dependency."""
from __future__ import annotations
import csv
import json
import math
from pathlib import Path

TYPES={'SWEEP_START','PHASE_RESULT','FREQ_RESULT','ERROR_SNAPSHOT','SWEEP_COMPLETE'}
FIELDS=('frequency_hz','d_phase','q_sample_phase','qm_sample_phase','d_phase_mdeg',
        'q_phase_mdeg','qm_phase_mdeg','pattern','requested_bits','total_bits','qm_total_bits',
        'q_errors','qm_errors','q_first_error_cycle','qm_first_error_cycle',
        'first_error_cycle','first_error_lane','first_error_expected','first_error_actual',
        'prbs_state','q_first_state','qm_first_state','q_start_state','qm_start_state')
LANE_FIELDS=('q_first_expected','q_first_actual','qm_first_expected','qm_first_actual')
STATUSES={'RUNNING','PASS','CAPTURE_ERRORS','ABORTED','UNSUPPORTED','BUILD_ERROR','TRANSPORT_ERROR','NO_VALID_CAPTURE_WINDOW'}

def parse_hs(obj):
    if type(obj.get('protocol_version')) is not int or obj.get('protocol_version')!=2 or obj.get('type') not in TYPES or obj.get('module')!='M11':
        raise ValueError('Invalid high-speed protocol/type/module')
    if obj.get('status') not in STATUSES:
        raise ValueError('Invalid high-speed status')
    for name in (*FIELDS,*(k for k in LANE_FIELDS if k in obj)):
        value=obj.get(name)
        if isinstance(value,str) and value.startswith('0x'):
            if not 1<=len(value[2:])<=16 or any(c not in '0123456789abcdefABCDEF' for c in value[2:]):
                raise ValueError(f'Invalid hexadecimal {name}')
            value=int(value,16)
        if type(value) is not int or not 0<=value<2**64:
            raise ValueError(f'Invalid unsigned 64-bit {name}')
        obj[name]=value
    if any(obj[k]>1 for k in LANE_FIELDS if k in obj):
        raise ValueError('Invalid per-lane snapshot bit')
    for lane in ('q','qm'):
        expected,actual=lane+'_first_expected',lane+'_first_actual'
        if expected in obj and actual in obj and obj[lane+'_errors'] and obj['type']!='SWEEP_START':
            if obj[expected]==obj[actual] or not 1<=obj[lane+'_first_error_cycle']<=obj['requested_bits']:
                raise ValueError('Invalid per-lane first error')
    if obj['frequency_hz']<=0 or obj['pattern'] not in (0,1,2,3,5):
        raise ValueError('Invalid frequency/pattern')
    if max(obj['d_phase'],obj['q_sample_phase'],obj['qm_sample_phase'])>15:
        raise ValueError('Invalid phase')
    if max(obj['d_phase_mdeg'],obj['q_phase_mdeg'],obj['qm_phase_mdeg'])>=360000:
        raise ValueError('Invalid configured phase angle')
    if obj['first_error_lane']>2 or max(obj['first_error_expected'],obj['first_error_actual'])>1:
        raise ValueError('Invalid error lane/bit')
    for key in ('prbs_state','q_first_state','qm_first_state','q_start_state','qm_start_state'):
        if obj[key]>=2**31:raise ValueError('Invalid PRBS31 state')
    if obj['q_errors']>obj['total_bits'] or obj['qm_errors']>obj['qm_total_bits']:
        raise ValueError('Error count exceeds samples')
    if obj['type']!='SWEEP_START' and obj['status'] in ('PASS','CAPTURE_ERRORS'):
        if obj['total_bits']!=obj['requested_bits'] or obj['qm_total_bits']!=obj['requested_bits'] or obj['total_bits']==0:
            raise ValueError('Incomplete high-speed result')
        if (obj['status']=='PASS') != (obj['q_errors']==obj['qm_errors']==0):
            raise ValueError('High-speed status/count mismatch')
    if obj['type']=='ERROR_SNAPSHOT':
        lane=obj['first_error_lane']
        if lane not in (1,2) or obj['first_error_cycle']==0 or obj['first_error_expected']==obj['first_error_actual']:
            raise ValueError('Invalid error snapshot')
    for key in ('voltage_v','temperature_c','pcb_delay_ns'):
        if obj.get(key) is not None and obj.get(key+'_source')!='measured':
            raise ValueError(f'{key} must be null unless measurement provenance is supplied')
        if obj.get(key) is not None and type(obj[key]) not in (int,float):
            raise ValueError(f'{key} must be numeric')
        if obj.get(key) is not None and not math.isfinite(obj[key]):
            raise ValueError(f'{key} must be finite')
    return obj

def window_center(good,minimum=3):
    """Longest circular run; absent/unsupported bins break the window."""
    good=set(good)
    if not good:return None
    if len(good)==16:return dict(center=7,bins=list(range(16)),width_bins=16)
    windows=[]
    for start in sorted(good):
        if (start-1)%16 in good:continue
        bins=[]
        while (start+len(bins))%16 in good and len(bins)<16:bins.append((start+len(bins))%16)
        if len(bins)>=minimum:windows.append(bins)
    if not windows:return None
    bins=max(windows,key=lambda b:(len(b),-b[0]))
    return dict(center=bins[(len(bins)-1)//2],bins=bins,width_bins=len(bins))

class HighSpeedAnalysis:
    def __init__(self,minimum_window_bins=3):
        self.records=[];self.minimum_window_bins=minimum_window_bins
    def add(self,record):self.records.append(dict(record))
    def windows(self,minimum=None):
        if minimum is None:minimum=self.minimum_window_bins
        phases=[r for r in self.records if r['type']=='PHASE_RESULT' and r['pattern']==5]
        out={}
        for frequency in sorted({r['frequency_hz'] for r in phases}):
            points=[r for r in phases if r['frequency_hz']==frequency]
            lanes={};classifications={}
            for lane,field in [('q','q_sample_phase'),('qm','qm_sample_phase')]:
                # A phase is good only if ALL repeated valid observations pass.
                by_phase={};unavailable=set()
                for p in points:
                    valid=p['status'] in ('PASS','CAPTURE_ERRORS') and p['total_bits']>0
                    by_phase.setdefault(p[field],[]).append(valid and p[lane+'_errors']==0)
                    if not valid:unavailable.add(p[field])
                good=[phase for phase,values in by_phase.items() if all(values)]
                lanes[lane]=window_center(good,minimum)
                labels={}
                for phase in range(16):
                    if phase not in by_phase or phase in unavailable:label='UNAVAILABLE'
                    elif phase in good:
                        label='SELECTED_VALID_WINDOW' if lanes[lane] and phase in lanes[lane]['bins'] else 'OTHER_ZERO_ERROR_PHASE'
                    elif lanes[lane]:
                        start,end=lanes[lane]['bins'][0],lanes[lane]['bins'][-1]
                        early=(start-phase)%16;late=(phase-end)%16
                        label='EARLY_SIDE_CANDIDATE' if early<late else ('LATE_SIDE_CANDIDATE' if late<early else 'EDGE_AMBIGUOUS')
                    else:label='NO_VALID_CAPTURE_WINDOW'
                    labels[str(phase)]=label
                classifications[lane]=labels
            lanes['status']='WINDOW_FOUND' if lanes['q'] and lanes['qm'] else 'NO_VALID_CAPTURE_WINDOW'
            if all(r['status']=='UNSUPPORTED' for r in points):lanes['status']='UNSUPPORTED'
            lanes['observed_bins']=len({r['q_sample_phase'] for r in points})
            lanes['observed_qm_bins']=len({r['qm_sample_phase'] for r in points})
            lanes['phase_classification']=classifications
            lanes['classification_interpretation']='Early/late are sides of the selected logical window, not a proven physical failure cause.'
            lanes['unsupported_points']=sum(r['status']=='UNSUPPORTED' for r in points)
            out[str(frequency)]=lanes
        return out
    def save(self,directory:Path,plots=True):
        directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
        windows=self.windows()
        columns=['type','test','source','selection_valid','frequency_hz','pattern','d_phase','q_sample_phase','qm_sample_phase',
                 'd_phase_mdeg','q_phase_mdeg','qm_phase_mdeg','requested_bits','total_bits',
                 'qm_total_bits','q_errors','qm_errors','q_error_rate','qm_error_rate','q_phase_class','qm_phase_class','status','reason']
        for kind,filename in [('PHASE_RESULT','phase_sweep.csv'),('FREQ_RESULT','frequency_sweep.csv')]:
            with (directory/filename).open('w',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader()
                for r in self.records:
                    if r['type']!=kind:continue
                    row={k:r.get(k) for k in columns}
                    row['source']=r.get('source','fpga')
                    row['selection_valid']=r.get('selection_valid',True)
                    row['q_error_rate']=r['q_errors']/r['total_bits'] if r['total_bits'] else None
                    row['qm_error_rate']=r['qm_errors']/r['qm_total_bits'] if r['qm_total_bits'] else None
                    for lane,field in [('q','q_sample_phase'),('qm','qm_sample_phase')]:
                        row[lane+'_phase_class']=windows.get(str(r['frequency_hz']),{}).get('phase_classification',{}).get(lane,{}).get(str(r[field]),'UNSCANNED')
                    if not row['selection_valid']:
                        for field in ('q_sample_phase','qm_sample_phase','q_phase_mdeg','qm_phase_mdeg'):row[field]=None
                        row['q_phase_class']=row['qm_phase_class']='NOT_SELECTED'
                    writer.writerow(row)
        identity=lambda r:tuple(r[k] for k in ('frequency_hz','q_sample_phase','qm_sample_phase','pattern'))
        rejected={identity(r) for r in self.records if r['type']=='FREQ_RESULT' and r['status']!='PASS' and r.get('selection_valid',True)}
        long=[r for r in self.records if r['type']=='FREQ_RESULT' and r['pattern']==5 and r['status']=='PASS' and r['total_bits']>=1000000 and identity(r) not in rejected]
        def verified(r):
            window=windows.get(str(r['frequency_hz']),{})
            return all(window.get(lane) and r[field] in window[lane]['bins'] for lane,field in [('q','q_sample_phase'),('qm','qm_sample_phase')])
        summary=dict(protocol_version=2,windows=windows,minimum_window_bins=self.minimum_window_bins,
                     highest_tested_zero_error_frequency_hz=max((r['frequency_hz'] for r in long),default=None),
                     highest_window_validated_zero_error_frequency_hz=max((r['frequency_hz'] for r in long if verified(r)),default=None),
                     zero_error_prbs_points=[dict(frequency_hz=r['frequency_hz'],bits=r['total_bits'],
                        q_sample_phase=r['q_sample_phase'],qm_sample_phase=r['qm_sample_phase'],
                        capture_window_verified=verified(r),
                        zero_error_95_upper_bound_approx=-math.log(.05)/r['total_bits']) for r in long],
                     interpretation='0 errors / N bits is an observation, not proof of zero theoretical BER',
                     upper_bound_assumptions='Approximate per-channel 95% bound assumes independent stationary Bernoulli errors; not a physical guarantee.',
                     clock_and_voltage='Frequency/phase are logic configurations. Voltage/temperature are unmeasured unless explicitly sourced.',
                     timing_provenance='Use runner_manifest.json to verify each programmed image passed internal FPGA timing; external delays are uncalibrated.',
                     complete_messages=sum(r['type']=='SWEEP_COMPLETE' for r in self.records),
                     aborted_points=sum(r['type'] in ('PHASE_RESULT','FREQ_RESULT') and r['status'] in ('ABORTED','BUILD_ERROR','TRANSPORT_ERROR') and r.get('test')!='SCAN_SUMMARY' for r in self.records),
                     unsupported_points=sum(r['type'] in ('PHASE_RESULT','FREQ_RESULT') and r['status']=='UNSUPPORTED' and r.get('test')!='SCAN_SUMMARY' for r in self.records))
        summary['no_valid_capture_window_frequencies_hz']=sorted({r['frequency_hz'] for r in self.records if r['type']=='FREQ_RESULT' and r['status']=='NO_VALID_CAPTURE_WINDOW'})
        summary['all_scanned_phases_unsupported_frequencies_hz']=sorted({r['frequency_hz'] for r in self.records if r.get('test')=='SCAN_SUMMARY' and r['status']=='UNSUPPORTED'})
        (directory/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        if plots:self.plot(directory)
        return summary
    def plot(self,directory):
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            (directory/'plot_status.json').write_text(json.dumps({'status':'MISSING_DEPENDENCY','install':'pip install -r requirements-analysis.txt'})+'\n')
            return
        freq=[r for r in self.records if r['type']=='FREQ_RESULT' and r['pattern']==5]
        fig,ax=plt.subplots(figsize=(8,4))
        for lane,marker in [('q','o'),('qm','s')]:
            x=[];y=[]
            for r in sorted(freq,key=lambda r:r['frequency_hz']):
                x.append(r['frequency_hz']/1e6)
                n=r['total_bits'] if lane=='q' else r['qm_total_bits']
                y.append(r[lane+'_errors']/n if n and r['status'] in ('PASS','CAPTURE_ERRORS') else float('nan'))
            ax.plot(x,y,marker=marker,label=lane.upper(),markerfacecolor='none',
                    markersize=9 if lane=='q' else 5,clip_on=False)
        ax.set(xlabel='Configured DUT clock / MHz',ylabel='Observed errors / bits',title='M11 frequency sweep (zero is an observation)');ax.grid(alpha=.3);ax.legend();ax.set_ylim(bottom=0)
        fig.tight_layout();fig.savefig(directory/'frequency_ber.png',dpi=160);plt.close(fig)
        phases=[r for r in self.records if r['type']=='PHASE_RESULT' and r['pattern']==5]
        hz=sorted({r['frequency_hz'] for r in phases})
        fig,axes=plt.subplots(2,1,figsize=(10,max(4,len(hz)*.55+2)),squeeze=False)
        for axis,lane,field in zip(axes[:,0],['q','qm'],['q_sample_phase','qm_sample_phase']):
            matrix=np.full((max(1,len(hz)),16),np.nan)
            for i,h in enumerate(hz):
                for phase in range(16):
                    group=[r for r in phases if r['frequency_hz']==h and r[field]==phase]
                    valid=group and all(r['status'] in ('PASS','CAPTURE_ERRORS') and r['total_bits'] and r['qm_total_bits'] for r in group)
                    if valid:matrix[i,phase]=max(r[lane+'_errors']/(r['total_bits'] if lane=='q' else r['qm_total_bits']) for r in group)
            cmap=plt.get_cmap('viridis').copy();cmap.set_bad('#dddddd')
            im=axis.imshow(matrix,aspect='auto',vmin=0,vmax=1,cmap=cmap)
            axis.set_xticks(range(16));axis.set_yticks(range(len(hz)),[f'{h/1e6:g}' for h in hz])
            axis.set(xlabel='Configured phase index / 16 turns',ylabel='Clock / MHz',title=f'{lane.upper()} observed error fraction (grey = unavailable)')
            fig.colorbar(im,ax=axis)
        fig.tight_layout();fig.savefig(directory/'phase_error.png',dpi=160);plt.close(fig)

def main(argv=None):
    import argparse
    from swcell_capture import parse_record
    p=argparse.ArgumentParser(description='Regenerate high-speed CSV, summary and plots from raw JSONL')
    p.add_argument('raw',type=Path);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--host-events',type=Path,help='Separate host UNSUPPORTED/transport events; auto-detected beside raw file')
    a=p.parse_args(argv);analysis=HighSpeedAnalysis()
    sources=[a.raw]
    host=a.host_events or a.raw.parent/'host_events.jsonl'
    if host.exists():sources.append(host)
    for source in sources:
        with source.open('rb') as f:
            for line in f:
                r=parse_record(line)
                if r.get('protocol_version')==2:analysis.add(r)
    print(json.dumps(analysis.save(a.output),indent=2))
    return 0

if __name__=='__main__':raise SystemExit(main())
