#!/usr/bin/env python3
"""Independent M11 phase scans, evidence-based windows and resumable JTAG runs.

Only static images passing implementation are programmed. Never writes Flash.
Offline: --analyze DIRECTORY. Hardware: --output DIRECTORY [--resume].
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime
import hashlib
import itertools
import json
import math
from functools import lru_cache
from pathlib import Path
import time

from swcell_capture import parse_record
from swcell_hs import HighSpeedAnalysis
from swcell_sweep import ROOT, build_point, fingerprint, run_hardware

FREQUENCIES=(75000000,100000000,125000000)
VALID={'PASS','CAPTURE_ERRORS'}

def atomic_json(path,value):
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
    temporary.replace(path)

def windows(good,lane,minimum=3):
    """Return EVERY zero-error run, with explicit expected-transaction cuts.

    Q: do not join 15->0, where b[n-1] changes to b[n].
    QM: cut 7->8 (held b[n-1] -> new b[n]); 15->0 is continuous b[n].
    These are reference-epoch rules, not guesses from measured error rates.
    """
    if lane not in ('q','qm'):raise ValueError('Unknown lane')
    good=set(good)
    if not good<=set(range(16)):raise ValueError('Invalid phase')
    order=list(range(16)) if lane=='q' else list(range(8,16))+list(range(8))
    runs=[];current=[]
    for p in order+[None]:
        if p in good:current.append(p)
        elif current:
            width=len(current)
            runs.append(dict(bins=current,center=current[(width-1)//2],width_bins=width,
                status='VALID_WINDOW' if width>=minimum else 'MARGINAL_WINDOW',
                boundary_censored=current[0]==order[0] or current[-1]==order[-1]))
            current=[]
    return sorted(runs,key=lambda w:(-w['width_bins'],w['bins'][0]))

def phase_points(hz,n,q_anchor=12,qm_anchor=6):
    return [('q',(hz,p,qm_anchor,n,5,1)) for p in range(16)]+[
            ('qm',(hz,q_anchor,p,n,5,1)) for p in range(16)]

def zero(result):
    return bool(result and result.get('status')=='PASS' and
                result['total_bits']==result['qm_total_bits']==result['requested_bits'] and
                result['q_errors']==result['qm_errors']==0)

@lru_cache(maxsize=256)
def adjacent_transitions(state,count):
    """Diagnostic only: mismatch count if this PRBS stream were one bit late."""
    previous=(state & 1)^((state>>28)&1)  # inverse of x^31+x^28+1 step
    errors=0
    for _ in range(count):
        bit=(state>>30)&1;errors+=bit!=previous;previous=bit
        state=((state<<1)&0x7fffffff)|(((state>>30)^(state>>27))&1)
    return errors

def timing_evidence(directory):
    directory=Path(directory)
    result=json.loads((directory/'timing_metrics.json').read_text())
    for key in ('wns_ns','whs_ns','wpws_ns'):
        if not math.isfinite(result[key]):raise ValueError('Invalid timing metric')
    for key in ('q_capture_loc','qm_capture_loc'):
        if not result[key].startswith('ILOGIC'):raise ValueError('Capture register is not in ILOGIC')
    # Report check_timing categories; external uncalibrated IO remains explicit.
    import re
    text=(directory/'timing.rpt').read_text()
    for key in ('no_clock','unconstrained_internal_endpoints','no_input_delay','no_output_delay'):
        match=re.search(r'checking '+key+r' \((\d+)\)',text)
        if not match:raise ValueError('Missing check_timing evidence '+key)
        result[key]=int(match[1])
    result['internal_timing_pass']=all(result[k]>=0 for k in ('wns_ns','whs_ns','wpws_ns')) and result['no_clock']==result['unconstrained_internal_endpoints']==0
    result['reports']={name:str(directory/(name+'.rpt')) for name in ('timing','clock_interaction','cdc','io','drc')}
    return result

def verify_job(job,directory):
    """A resume trusts complete raw envelopes, counts, hashes and image identity."""
    if job['status']!='MEASURED':return
    raw_path=directory/job['raw_file'];data=raw_path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=job['raw_sha256']:raise ValueError('Raw checksum mismatch '+job['id'])
    records=[parse_record(line) for line in data.splitlines()]
    kind='PHASE_RESULT' if job['point'][5] else 'FREQ_RESULT'
    if not records or records[0]['type']!='SWEEP_START' or records[-1]['type']!='SWEEP_COMPLETE':
        raise ValueError('Incomplete saved UART envelope '+job['id'])
    results=[r for r in records if r['type']==kind]
    if len(results)!=1 or results[0]!=job['result']:raise ValueError('Saved result/raw mismatch '+job['id'])
    expected=tuple(job['point'][:5])
    for record in records:
        identity=tuple(record[k] for k in ('frequency_hz','q_sample_phase','qm_sample_phase','requested_bits','pattern'))
        if identity!=expected:raise ValueError('Saved UART identity mismatch '+job['id'])
    if not job['timing']['internal_timing_pass']:raise ValueError('Measured unsupported image')
    bit=Path(job['build_dir'])/'swcell_m11_hs_top.bit'
    # Offline export works after large image caches have been archived/deleted.
    if bit.exists() and hashlib.sha256(bit.read_bytes()).hexdigest()!=job['bitstream_sha256']:
        raise ValueError('Bitstream checksum mismatch '+job['id'])

def latest_jobs(state):
    out={}
    for job in state['attempts']:out[job['id']]=job
    return list(out.values())

def frequency_summary(hz,jobs,minimum):
    phase={lane:[j for j in jobs if j['point'][0]==hz and j['stage']==lane] for lane in ('q','qm')}
    result={'frequency_hz':hz,'windows':{},'complete':{},'measured_complete':{},'unsupported_phases':{},'selected_pairs':[]}
    for lane in ('q','qm'):
        measured=[j for j in phase[lane] if j['status']=='MEASURED']
        good=[j['point'][1 if lane=='q' else 2] for j in measured if j['result'][lane+'_errors']==0]
        result['windows'][lane]=windows(good,lane,minimum)
        index=1 if lane=='q' else 2
        attempted={j['point'][index] for j in phase[lane] if j['status'] in ('MEASURED','UNSUPPORTED')}
        result['complete'][lane]=len(attempted)==16
        result['measured_complete'][lane]=len(measured)==16
        result['unsupported_phases'][lane]=[dict(phase_index=j['point'][index],reason=j.get('reason')) for j in phase[lane] if j['status']=='UNSUPPORTED']
    long=[j for j in jobs if j['point'][0]==hz and j['stage'] in ('million','hundred_million') and j['status']=='MEASURED']
    reliable=lambda j:all(any(w['center']==j['point'][i] and w['status']=='VALID_WINDOW' for w in result['windows'][lane]) for lane,i in (('q',1),('qm',2)))
    def prerequisites(j):
        pair=j['point'][1:3]
        stages=[x for x in jobs if x['point'][0]==hz and x['point'][1:3]==pair and x['status']=='MEASURED']
        return (all(any(x['stage']=='alignment' and x['point'][4]==p and zero(x['result']) for x in stages) for p in (2,3)) and
                any(x['stage']=='million' and zero(x['result']) for x in stages))
    hundred=[j for j in long if j['stage']=='hundred_million' and zero(j['result']) and reliable(j) and prerequisites(j)]
    million=[j for j in long if j['stage']=='million' and zero(j['result']) and reliable(j) and prerequisites(j)]
    result['observed_zero_error_1e8_pairs']=[dict(q=j['point'][1],qm=j['point'][2],test_id=j['id'])
        for j in long if j['stage']=='hundred_million' and zero(j['result']) and prerequisites(j)]
    for j in long:
        if zero(j['result']):result['selected_pairs'].append(dict(q=j['point'][1],qm=j['point'][2],bits=j['point'][3],test_id=j['id']))
    if not all(result['complete'].values()):status='INCONCLUSIVE'
    elif hundred:status='PASS_1E8_ZERO_ERRORS'
    elif million and not any(j['stage']=='hundred_million' for j in long) and all(result['complete'].values()):status='PASS_1E6_ONLY'
    elif any(not result['windows'][lane] for lane in ('q','qm')):
        if any(j['status']=='UNSUPPORTED' for lane in phase.values() for j in lane):status='FPGA_TIMING_FAILURE'
        elif all(result['complete'].values()):status='NO_VALID_CAPTURE_WINDOW'
        else:status='INCONCLUSIVE'
    elif any(all(w['status']=='MARGINAL_WINDOW' for w in result['windows'][lane]) for lane in ('q','qm')):status='MARGINAL_WINDOW'
    else:status='INCONCLUSIVE'
    result['status']=status
    result['interpretation']='No DUT failure is inferred solely from a missing capture window or a one-cycle transition signature.'
    return result

def export(directory,state,plots=True):
    jobs=latest_jobs(state)
    for job in jobs:verify_job(job,directory)
    phase=[];long=[]
    for j in jobs:
        hz,q,m,n,pattern,scan=j['point'];r=j.get('result',{});timing=j.get('timing',{})
        common=dict(test_id=j['id'],frequency_hz=hz,status=j['status'],pattern=pattern,
            q_phase_index=q,qm_phase_index=m,bitstream_sha256=j.get('bitstream_sha256'),
            build_dir=j.get('build_dir'),raw_file=j.get('raw_file'),
            wns_ns=timing.get('wns_ns'),whs_ns=timing.get('whs_ns'),wpws_ns=timing.get('wpws_ns'),
            timing_status='INTERNAL_PASS_EXTERNAL_UNCALIBRATED' if timing.get('internal_timing_pass') else j['status'])
        if scan:
            lane=j['stage'];p=q if lane=='q' else m
            total=r.get('total_bits' if lane=='q' else 'qm_total_bits');errors=r.get(lane+'_errors')
            transition_count=adjacent_transitions(r[lane+'_start_state'],total) if total and pattern==5 else None
            phase.append(dict(common,signal=lane.upper(),phase_index=p,phase_ps=1e12*p/(hz*16),
                phase_source='MMCM_CONFIG_CALCULATED_NOT_EXTERNAL_MEASUREMENT',total_checks=total,error_checks=errors,
                error_rate=errors/total if total else None,status=('ZERO_ERRORS' if errors==0 else 'CAPTURE_ERRORS') if j['status']=='MEASURED' else j['status'],
                first_error_cycle=r.get(lane+'_first_error_cycle'),first_error_expected=r.get(lane+'_first_expected'),first_error_actual=r.get(lane+'_first_actual'),
                adjacent_bit_transition_count=transition_count,one_cycle_signature_candidate=bool(errors and errors==transition_count)))
        else:
            total=r.get('total_bits');mt=r.get('qm_total_bits');qe=r.get('q_errors');me=r.get('qm_errors')
            long.append(dict(common,stage=j['stage'],total_bits=total,qm_total_bits=mt,q_errors=qe,qm_errors=me,
                q_error_rate=qe/total if total else None,qm_error_rate=me/mt if mt else None,
                elapsed_seconds=j.get('wall_seconds'),elapsed_source='HOST_JTAG_UART_WALL_TIME',
                effective_data_seconds=n/hz if j['status']=='MEASURED' else None,
                q_first_error_cycle=r.get('q_first_error_cycle'),qm_first_error_cycle=r.get('qm_first_error_cycle'),
                q_first_expected=r.get('q_first_expected'),q_first_actual=r.get('q_first_actual'),
                qm_first_expected=r.get('qm_first_expected'),qm_first_actual=r.get('qm_first_actual'),
                q_first_state=r.get('q_first_state'),qm_first_state=r.get('qm_first_state'),
                status=r.get('status',j['status'])))
    def write_csv(name,rows,required):
        fields=list(dict.fromkeys(required+[key for row in rows for key in row]))
        with (directory/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    write_csv('phase_scan.csv',phase,['test_id','frequency_hz','signal','phase_index','phase_ps','total_checks','error_checks','error_rate','status'])
    write_csv('long_run.csv',long,['frequency_hz','q_phase_index','qm_phase_index','total_bits','q_errors','qm_errors','elapsed_seconds','timing_status','status'])
    summaries=[frequency_summary(hz,jobs,state['config']['minimum_window_bins']) for hz in state['config']['frequencies']]
    passed=[s['frequency_hz'] for s in summaries if s['status']=='PASS_1E8_ZERO_ERRORS']
    observed=[s['frequency_hz'] for s in summaries if s['observed_zero_error_1e8_pairs']]
    summary=dict(protocol='M11_PHASE2B_ANALYSIS_1',source_sha256=state['source_sha256'],frequencies=summaries,
        highest_tested_1e8_zero_error_frequency_hz=max(passed,default=None),runner_status=state['status'],
        highest_observed_1e8_zero_error_frequency_hz=max(observed,default=None),
        highest_frequency_interpretation='highest_tested requires reliable scan windows; highest_observed may include MARGINAL_WINDOW, never device guaranteed Fmax.',
        metadata=state['config'],attempts=len(state['attempts']),active_jobs=len(jobs),
        firmware_versions=sorted({j['result']['fpga_version'] for j in jobs if j.get('result',{}).get('fpga_version')}),
        voltage_v=None,temperature_c=None,voltage_nominal_v=3.3,
        phase_interpretation='Configured ideal MMCM phase, not calibrated PCB/157/IO propagation delay.',
        zero_error_interpretation='0 errors / N checks is an observation, not theoretical BER=0.')
    atomic_json(directory/'summary.json',summary)
    if plots:make_plots(directory,phase,summaries)
    lines=['# M11 Phase 2B 测试记录','',f"源码 SHA256：`{state['source_sha256']}`",'',
        '相位为 MMCM 配置推导值，未做板外绝对延迟标定。零错误只表示本轮 N 次检查没有观察到错误。','',
        '|频率 MHz|Q 有效窗口（索引）|QM 有效窗口（索引）|结论|','|---:|---|---|---|']
    for s in summaries:
        fmt=lambda lane:'; '.join(','.join(map(str,w['bins']))+' → '+str(w['center'])+' ('+w['status']+')' for w in s['windows'][lane]) or '无/未完成'
        lines.append(f"|{s['frequency_hz']/1e6:g}|{fmt('q')}|{fmt('qm')}|{s['status']}|")
    lines+=['','![Q scan](q_phase_scan.png)','','![QM scan](qm_phase_scan.png)','','![Frequency summary](frequency_summary.png)','',
        '逐点计数、首错和时序见 phase_scan.csv；候选模式、百万次及亿次见 long_run.csv。elapsed_seconds 包含 JTAG/UART 开销；effective_data_seconds=N/f 是配置推导的有效数据时长。',
        '原始 UART 字节保存在 raw.jsonl 和 attempts/；checkpoint.json 保存每次尝试、校验值及构建路径。未完成测试保留为空，不按零错误处理。']
    (directory/'report.md').write_text('\n'.join(lines)+'\n')
    return summary

def make_plots(directory,phase,summaries):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    for lane in ('q','qm'):
        fig,axes=plt.subplots(len(summaries),1,figsize=(10,3*len(summaries)),squeeze=False)
        for ax,s in zip(axes[:,0],summaries):
            hz=s['frequency_hz'];points={r['phase_index']:r for r in phase if r['frequency_hz']==hz and r['signal']==lane.upper()}
            x=list(range(16));y=[points.get(i,{}).get('error_rate') for i in x]
            ax.plot(x,[math.nan if v is None else v for v in y],'o-',label='Measured digital error ratio')
            for window in s['windows'][lane]:
                for p in window['bins']:ax.axvspan(p-.45,p+.45,color='orange' if window['status']=='MARGINAL_WINDOW' else 'green',alpha=.12)
                ax.axvline(window['center'],color='green',ls=':',alpha=.6)
            selected={pair[lane] for pair in s['selected_pairs']}
            for p in selected:ax.plot(p,points[p]['error_rate'],'*',ms=14,color='red')
            ax.set(xticks=x,ylim=(-.03,1.03),ylabel='Errors / checks',title=f'{hz/1e6:g} MHz — {lane.upper()} (green=candidate, red star=tested selection)')
            ax.grid(alpha=.25);ax.set_xlabel('Configured phase index (1 bin = T/16; not measured absolute delay)')
        fig.tight_layout();fig.savefig(directory/(lane+'_phase_scan.png'),dpi=150);plt.close(fig)
    fig,ax=plt.subplots(figsize=(11,3))
    colors={'PASS_1E8_ZERO_ERRORS':'green','PASS_1E6_ONLY':'olive','MARGINAL_WINDOW':'orange','NO_VALID_CAPTURE_WINDOW':'red','FPGA_TIMING_FAILURE':'purple','INCONCLUSIVE':'gray'}
    for i,s in enumerate(summaries):
        ax.barh(i,1,color=colors.get(s['status'],'gray'),alpha=.7)
        ax.text(.02,i,s['status'],va='center',color='white',weight='bold')
    ax.set(yticks=range(len(summaries)),yticklabels=[f"{s['frequency_hz']/1e6:g} MHz" for s in summaries],xticks=[],title='Observed verification status (not device Fmax)')
    fig.tight_layout();fig.savefig(directory/'frequency_summary.png',dpi=150);plt.close(fig)

class Runner:
    def __init__(self,args,directory,state):
        self.args=args;self.directory=directory;self.state=state;self.futures={}
    def save(self):
        self.state['updated_at']=datetime.now().astimezone().isoformat()
        atomic_json(self.directory/'checkpoint.json',self.state)
    def measure(self,stage,point):
        key=stage+'_'+'_'.join(map(str,point));old=next((j for j in reversed(self.state['attempts']) if j['id']==key),None)
        if old and old['status'] in ('MEASURED','UNSUPPORTED'):
            verify_job(old,self.directory);return old.get('result')
        job=dict(id=key,stage=stage,point=list(point),status='STARTED',started_at=datetime.now().astimezone().isoformat())
        self.state['attempts'].append(job);self.save()
        try:
            out,status=self.futures[point].result() if point in self.futures else build_point(point,self.args)
            job.update(build_dir=str(out),status=status['status'],reason=status['reason'])
            if (out/'timing_metrics.json').exists():job['timing']=timing_evidence(out)
            if status['status']!='SUPPORTED':return None
            if not job['timing']['internal_timing_pass']:raise ValueError('Internal timing evidence failed')
            if self.args.build_only:return None
            job['bitstream_sha256']=hashlib.sha256((out/'swcell_m11_hs_top.bit').read_bytes()).hexdigest()
            raw_path=self.directory/'attempts'/f"{len(self.state['attempts']):04d}_{key}.jsonl"
            raw_path.parent.mkdir(exist_ok=True);job['raw_file']=str(raw_path.relative_to(self.directory))
            began=time.monotonic();analysis=HighSpeedAnalysis()
            try:
                with raw_path.open('wb') as raw:result=run_hardware(point,out,self.args,raw,analysis)
            finally:
                job['wall_seconds']=time.monotonic()-began
                data=raw_path.read_bytes();job['raw_sha256']=hashlib.sha256(data).hexdigest()
                with (self.directory/'raw.jsonl').open('ab') as all_raw:
                    job['raw_offset']=all_raw.tell();all_raw.write(data);job['raw_length']=len(data)
            if any(k not in result for k in ('q_first_expected','q_first_actual','qm_first_expected','qm_first_actual')):
                raise ValueError('Phase2B requires independent first-error fields')
            job.update(status='MEASURED',result=result)
            verify_job(job,self.directory)
            return result
        except KeyboardInterrupt:
            job['status']='INTERRUPTED';raise
        except Exception as exc:
            job.update(status='INFRASTRUCTURE_ERROR',reason=str(exc));print('POINT ERROR',key,str(exc),flush=True)
            return None
        finally:
            self.save();export(self.directory,self.state,plots=False)
    def frequency(self,hz):
        cfg=self.state['config']
        for lane,point in phase_points(hz,cfg['scan_bits'],cfg['q_anchor'],cfg['qm_anchor']):self.measure(lane,point)
        if self.args.build_only:return
        s=frequency_summary(hz,latest_jobs(self.state),cfg['minimum_window_bins'])
        # Both full axes are attempted before selection, even if the other fails.
        if not all(s['complete'].values()) or cfg.get('scan_only'):return
        for qw,mw in itertools.product(s['windows']['q'],s['windows']['qm']):
            q,m=qw['center'],mw['center']
            # Validate cycle correspondence with patterns of periods 2 and 4.
            alignment=[self.measure('alignment',(hz,q,m,cfg['scan_bits'],pattern,0)) for pattern in (2,3)]
            million=self.measure('million',(hz,q,m,1000000,5,0))
            if all(zero(r) for r in alignment) and zero(million):
                self.measure('hundred_million',(hz,q,m,100000000,5,0))
            else:print('GATE CLOSED',hz,q,m,'No 1e8: alignment or 1e6 failed/unavailable',flush=True)

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path);p.add_argument('--resume',action='store_true')
    p.add_argument('--analyze',type=Path);p.add_argument('--frequencies',default='75000000,100000000,125000000')
    p.add_argument('--scan-bits',type=int,default=10000);p.add_argument('--minimum-window-bins',type=int,default=3)
    p.add_argument('--q-anchor',type=int,default=12);p.add_argument('--qm-anchor',type=int,default=6)
    p.add_argument('--jobs',type=int,default=3,help='Concurrent independent Vivado builds; JTAG remains serial')
    p.add_argument('--build-only',action='store_true');p.add_argument('--rebuild',action='store_true')
    p.add_argument('--scan-only',action='store_true',help='Measure both axes without new long runs (optional 50MHz baseline)')
    p.add_argument('--port',default='/dev/ttyUSB1');p.add_argument('--baud',type=int,default=115200)
    p.add_argument('--device',default='xc7k325t_0');p.add_argument('--vivado',default='vivado')
    p.add_argument('--build-timeout',type=int,default=1800);p.add_argument('--program-timeout',type=int,default=120)
    args=p.parse_args(argv)
    if args.analyze:
        state=json.loads((args.analyze/'checkpoint.json').read_text());export(args.analyze,state);return 0
    try:frequencies=list(map(int,args.frequencies.split(',')))
    except ValueError:p.error('Invalid frequency list')
    if not frequencies or len(set(frequencies))!=len(frequencies) or any(f not in FREQUENCIES+(50000000,) for f in frequencies):p.error('Frequencies: 50/75/100/125 MHz only')
    if not 4096<=args.scan_bits<=1000000000 or not 3<=args.minimum_window_bins<=16:p.error('Scan >=4096; conservative reliable window needs >=3 bins')
    if args.q_anchor not in range(16) or args.qm_anchor not in range(16) or not 1<=args.jobs<=4 or args.baud!=115200:p.error('Invalid anchor/jobs/baud')
    directory=args.output or ROOT/'results/M11'/datetime.now().astimezone().strftime('phase2b_%Y%m%d_%H%M%S_%f%z')
    if args.resume:
        if not args.output:p.error('--resume requires --output')
        if args.rebuild:p.error('Use a new output directory for forced rebuilds; saved image checksums must remain immutable')
        state=json.loads((directory/'checkpoint.json').read_text())
        if state['source_sha256']!=fingerprint():p.error('Source fingerprint differs; start a new run')
        if any(hz not in state['config']['frequencies'] for hz in frequencies):p.error('Resume frequencies must be a subset of original run')
        for name in ('scan_bits','minimum_window_bins','q_anchor','qm_anchor'):
            if state['config'][name]!=getattr(args,name):p.error('Resume configuration mismatch: '+name)
        if bool(state['config'].get('scan_only'))!=args.scan_only:p.error('Resume scan-only configuration mismatch')
        for job in latest_jobs(state):verify_job(job,directory)
    else:
        directory.mkdir(parents=True,exist_ok=False)
        state=dict(schema_version=1,source_sha256=fingerprint(),status='RUNNING',started_at=datetime.now().astimezone().isoformat(),attempts=[],
            config=dict(frequencies=frequencies,scan_bits=args.scan_bits,minimum_window_bins=args.minimum_window_bins,
                        q_anchor=args.q_anchor,qm_anchor=args.qm_anchor,scan_only=args.scan_only,device='xc7k325tffg900-2',system_clock_hz=50000000,uart_baud=115200,
                        io_standard='LVCMOS33',drive_ma=12,slew='SLOW'))
    print('OUTPUT',directory,flush=True)
    runner=Runner(args,directory,state);runner.save();state['status']='RUNNING';code=0
    pool=ThreadPoolExecutor(max_workers=args.jobs)
    try:
        for hz in frequencies:
            # Prefetch only this frequency. Every scan future is consumed before
            # synchronous gated long-run builds begin, so those builds cannot
            # exceed --jobs by competing with the next frequency's prefetch.
            # The two axes share their anchor intersection's immutable image.
            finished={j['id'] for j in latest_jobs(state) if j['status'] in ('MEASURED','UNSUPPORTED')}
            points=dict.fromkeys(point for stage,point in phase_points(hz,args.scan_bits,args.q_anchor,args.qm_anchor)
                                 if stage+'_'+'_'.join(map(str,point)) not in finished)
            runner.futures={point:pool.submit(build_point,point,args) for point in points}
            runner.frequency(hz);export(directory,state)
        state['status']='BUILD_COMPLETE' if args.build_only else 'COMPLETE'
    except KeyboardInterrupt:
        state['status']='INTERRUPTED';code=130
        print('Interrupted; partial raw data retained. Resume skips verified completed measurements.',flush=True)
    finally:
        # Pending builds cancel; active vendor processes finish their isolated image.
        pool.shutdown(wait=True,cancel_futures=True)
        runner.save();summary=export(directory,state)
    if code:return code
    if args.build_only:return 0 if not any(j['status']=='INFRASTRUCTURE_ERROR' for j in latest_jobs(state)) else 2
    return 0 if all(s['status']=='PASS_1E8_ZERO_ERRORS' for s in summary['frequencies']) else 1

if __name__=='__main__':raise SystemExit(main())
