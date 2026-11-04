"""Prepare independent pin-delay cases and classify measured XSIM results.

No case is NC7SZ157 physical timing signoff. Fast chain has no excluded minimum
in current datasheet; it is retained as an unqualified-min sensitivity corner,
not silently discarded as an irrelevant malformed-input test.
"""
import argparse,csv,hashlib,json,re
from pathlib import Path
from copy import deepcopy
ROOT=Path(__file__).resolve().parents[3]
TAPS=(4,8,12,16)
SCENARIOS=('nominal','independent_cross','master_late','slave_late','mixed_stage','edge_asymmetric','decode_hold_mismatch','buffer_skew','duty_jitter','probe_load','safe_hold_normal','safe_hold_late_release','runt_high','fast_chain_sensitivity')

def config(name,tap):
 gate=[dict(dr=2.,df=2.,sr=1.,sf=1.) for _ in range(16)] + [dict(dr=1.,df=1.,sr=1.,sf=1.) for _ in range(4)]
 leaf=[dict(bmr=2.,bmf=2.,bsr=2.,bsf=2.,mo=1.,mc=1.,so=1.,sc=1.,mdr=.1,mdf=.1,sdr=.1,sdf=.1) for _ in range(33)]
 mode=0;high=500.;low=500.;jitter=0.;guard=4.;role='normal_assumed';extra=[]
 if name in ('independent_cross','mixed_stage','edge_asymmetric','probe_load','fast_chain_sensitivity'):
  gate[16]['sr']=4.;gate[17]['sf']=4.
  for i,v in enumerate(leaf):
   b=1.+3.*i/32;d=1.+4.*i/32
   for k in ('bmr','bmf','bsr','bsf'):v[k]=b
   for k in ('mo','mc','so','sc'):v[k]=d
 if name=='master_late':
  mode=1;gate[16]['sr']=4.
  for v in leaf:v.update(bmr=4.,mc=5.,bsr=1.,so=1.,bmf=1.,mo=1.,bsf=1.,sc=1.)
 if name=='slave_late':
  mode=2;gate[17]['sf']=4.
  for v in leaf:v.update(bmr=1.,mc=1.,bsr=1.,so=1.,bmf=1.,mo=1.,bsf=4.,sc=5.)
 if name=='mixed_stage':
  for i,v in enumerate(gate[:16]):v.update(dr=(.5 if i%2==0 else 3.5),df=(3.,.5,2.,1.)[i%4])
 if name=='edge_asymmetric':
  for v in gate[:16]:v['df']=1.
 if name=='decode_hold_mismatch':
  gate[16].update(sr=5.2,df=.5);gate[17].update(sf=5.2,dr=.5)
  gate[18].update(dr=5.,df=.5);gate[19].update(df=5.,dr=.5)
  for v in leaf:v.update(bmr=4.,mc=5.,bsr=1.,so=1.,bmf=1.,mo=1.,bsf=4.,sc=5.)
 if name=='buffer_skew':
  for i,v in enumerate(leaf):
   for k in ('bmr','bmf','bsr','bsf'):v[k]=12.*i/32
 if name=='duty_jitter':high=300.;low=700.;jitter=20.
 if name=='probe_load':
  # Explicit sensitivity assumption; no RC extraction or calibrated ns/pF claim.
  gate[tap-1]['dr']+=1.;gate[tap-1]['df']+=2.
  extra.append(dict(node=f'TAP{tap}',extra_probe_pf=5.,assumed_rise_ns_per_pf=.2,assumed_fall_ns_per_pf=.4))
 if name=='safe_hold_normal':
  mode=3;gate[18].update(sr=4.5,sf=.7);gate[19].update(sr=.5,sf=5.)
 if name=='safe_hold_late_release':mode=4;gate[18]['sf']=12.;role='negative_control_contract'
 if name=='runt_high':high=3.;role='negative_input_contract'
 if name=='fast_chain_sensitivity':
  for v in gate[:16]:v.update(dr=.5,df=.5)
  role='unqualified_minimum_sensitivity'
 chain_r=sum(gate[i]['dr'] for i in range(tap));chain_f=sum(gate[i]['df'] for i in range(tap))
 h_rise=min(gate[16]['sr'],chain_r+gate[16]['dr'])
 s_rise=max(gate[17]['sr'],chain_r+gate[17]['dr'])
 s_fall=min(gate[17]['sf'],chain_f+gate[17]['df'])
 h_fall=max(gate[16]['sf'],chain_f+gate[16]['df'])
 mclose=[h_rise+gate[18]['dr']+v['bmr']+v['mc'] for v in leaf]
 sopen=[s_rise+gate[19]['dr']+v['bsr']+v['so'] for v in leaf]
 sclose=[s_fall+gate[19]['df']+v['bsf']+v['sc'] for v in leaf]
 mopen=[h_fall+gate[18]['df']+v['bmf']+v['mo'] for v in leaf]
 branches=[]
 for b in range(6):
  items=[leaf[i] for i in range(33) if i%6==b]
  branches.append(dict(index=b,leaf_indices=[i for i in range(33) if i%6==b],base_ns={k:min(v[k] for v in items) for k in ('bmr','bmf','bsr','bsf')}))
 for i,v in enumerate(leaf):
  v['branch_index']=i%6
  v['within_branch_skew_ns']={k:v[k]-branches[i%6]['base_ns'][k] for k in ('bmr','bmf','bsr','bsf')}
 return dict(name=name,tap=tap,mode=mode,high_ns=high,low_ns=low,jitter_ns=jitter,guard_ns=guard,
  role=role,buffer_branches=branches,parameters_classification='assumed_not_datasheet_guarantees',gates=gate,leaves=leaf,load_sensitivity=extra,
  loads=dict(selected_tap_direct_mux_inputs=2+int(tap<16),unselected_later_stages='all instantiated; not all in parallel at selected tap',pad_trace_probe_pf=None),
  predicted_full_pulse_d1_ns=min(sopen)-max(mclose),predicted_full_pulse_d2_ns=min(mopen)-max(sclose),
  own_d1_min_ns=min(a-b for a,b in zip(sopen,mclose)),own_d2_min_ns=min(a-b for a,b in zip(mopen,sclose)))

def checked(path,fresh=False):
 p=Path(path).resolve();base=ROOT/'build/m20_300/v24_ff16'
 if base not in p.parents or (fresh and p.exists()):raise ValueError('requires fresh child of build/m20_300/v24_ff16')
 return p

def sources():
 paths=[]
 for folder in ('rtl/m20/v24_ff16','sim/m20_ff16','sim/m20_ff16_static'):
  paths += [p for p in (ROOT/folder).rglob('*') if p.is_file()]
 paths += [ROOT/'host/python/m20/ff16_timing.py',ROOT/'host/python/m20/ff16_structure.py',ROOT/'sim/scripts/run_m20_ff16_small.sh']
 return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}

def input_hashes(out):
 paths=[]
 for tap in TAPS:
  d=out/f'tap{tap}';paths.append(d/'cases.txt')
  for name in SCENARIOS:paths += [d/f'{name}.cfg',d/f'{name}.json']
 return {str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

def prepare(path):
 out=checked(path,True);out.mkdir(parents=True)
 for tap in TAPS:
  d=out/f'tap{tap}';d.mkdir();lines=[]
  for name in SCENARIOS:
   cfg=config(name,tap);p=d/f'{name}.cfg';gkeys=('dr','df','sr','sf');lkeys=('bmr','bmf','bsr','bsf','mo','mc','so','sc','mdr','mdf','sdr','sdf')
   text=' '.join(str(cfg[k]) for k in ('mode','high_ns','low_ns','jitter_ns','guard_ns'))+'\n'
   text+=''.join(' '.join(str(v[k]) for k in gkeys)+'\n' for v in cfg['gates'])
   text+=''.join(' '.join(str(v[k]) for k in lkeys)+'\n' for v in cfg['leaves']);p.write_text(text)
   (d/f'{name}.json').write_text(json.dumps(cfg,indent=2)+'\n');lines.append(name+' '+str(p))
  (d/'cases.txt').write_text('\n'.join(lines)+'\n')
 (out/'input_sha256.json').write_text(json.dumps(input_hashes(out),indent=2)+'\n')
 (out/'source_sha256.json').write_text(json.dumps(sources(),indent=2)+'\n')
 print('FF16_SMALL_PREPARED taps=4 cases_per_tap='+str(len(SCENARIOS)))

def summarize(path):
 out=checked(path)
 if sources()!=json.loads((out/'source_sha256.json').read_text()):raise ValueError('timing sources changed DURING run')
 if input_hashes(out)!=json.loads((out/'input_sha256.json').read_text()):raise ValueError('input/config files changed DURING run')
 structure=json.loads((out/'structure/structure_audit.json').read_text())
 if structure['status']!='VERIFIED' or any(v['physical_mux_count']!=20 for v in structure['profiles']):raise ValueError('structural audit not verified')
 for name,marker in (('pin_model','FF16_PIN_MODEL_VERIFIED'),('structure','FF16_STATIC_LOGIC_VERIFIED vectors=24')):
  if marker not in (out/'xsim'/f'{name}.log').read_text():raise ValueError('missing actual selftest '+name)
 rows=[]
 for tap in TAPS:
  d=out/f'tap{tap}'
  with (d/f'results_tap{tap}.csv').open() as f:raw=list(csv.DictReader(f))
  if [v['case'] for v in raw]!=list(SCENARIOS):raise ValueError('incomplete/duplicate/unexpected raw cases')
  if f'FF16_SMALL_COMPLETE tap={tap} cases={len(SCENARIOS)}' not in (out/'xsim'/f'tap{tap}.log').read_text():raise ValueError('missing actual timing completion')
  for row in raw:
   cfg=config(row['case'],tap)
   for k in ('d1_ns','d2_ns','min_master_window_ns'):row[k]=float(row[k])
   for k in ('tap','global_overlap_events','own_overlap_events','data_errors','pipeline_errors','penetration_events','missing_windows','guard_fail','master_index','slave_index','short_master_windows','d2_master_index','d2_slave_index'):row[k]=int(row[k])
   if row['case'] not in ('runt_high','safe_hold_late_release'):
    if row['missing_windows']:raise ValueError('unexpected missing edge '+str(row))
    for measure,predict in (('d1_ns','predicted_full_pulse_d1_ns'),('d2_ns','predicted_full_pulse_d2_ns')):
     if abs(row[measure]-cfg[predict])>.02:raise ValueError('measured/predicted mismatch '+str(row))
   for key in ('d1_ns','d2_ns','min_master_window_ns'):
    if row[key]>1e20:row[key]=None
   failure=row['global_overlap_events'] or row['data_errors'] or row['pipeline_errors'] or row['missing_windows'] or row['guard_fail']
   row.update(status='FAILED' if failure else 'CONDITIONAL',role=cfg['role'])
   rows.append(row)
 # Required model witnesses: negative own-bit data penetration in BOTH directions,
 # and cross-register race without own-bit overlap. A missing witness is engine FAIL.
 for case in ('master_late','slave_late'):
  r=next(v for v in rows if v['tap']==4 and v['case']==case)
  if not(r['global_overlap_events'] and r['penetration_events'] and r['data_errors']):raise ValueError('missing direct penetration witness '+str(r))
 r=next(v for v in rows if v['tap']==4 and v['case']=='independent_cross')
 if not(r['global_overlap_events'] and r['own_overlap_events']==0 and r['pipeline_errors']):raise ValueError('missing cross-register witness '+str(r))
 for tap in TAPS:
  for name in ('nominal','safe_hold_normal'):
   if next(v for v in rows if v['tap']==tap and v['case']==name)['status']!='CONDITIONAL':raise ValueError('positive model failure '+name)
  if next(v for v in rows if v['tap']==tap and v['case']=='safe_hold_late_release')['status']!='FAILED':raise ValueError('unsafe release not detected')
 # Preserve inadmissible-min sensitivity as a blocking engineering result.
 sensitivity=[v for v in rows if v['case']=='fast_chain_sensitivity']
 stop=all(v['d1_ns']<0 or v['d2_ns']<0 for v in sensitivity)
 with (out/'timing_results.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 result=dict(structure_status='VERIFIED_SEPARATE_AUDIT',model_witness_status='VERIFIED',timing_status='CONDITIONAL_ONLY',
  project_gate='STOP_BEFORE_C_AND_D' if stop else 'REVIEW_REQUIRED',cases=len(rows),positive_conditional=sum(v['status']=='CONDITIONAL' for v in rows),failed_cases=sum(v['status']=='FAILED' for v in rows),
  all_taps_fail_unknown_minimum_sensitivity=stop,physical_status='NOT_VERIFIED',cpu_integration='NOT_RUN',recommended_physical_tap=None,
  note='Assumed independent arcs, not physical corners; do not silently exclude unqualified minimum sensitivity.',results=rows)
 (out/'small_verification.json').write_text(json.dumps(result,indent=2)+'\n')
 print('FF16_MODEL_WITNESSES_VERIFIED project_gate='+result['project_gate'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=('prepare','summarize'));p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 try:{'prepare':prepare,'summarize':summarize}[a.command](a.output)
 except (OSError,ValueError,AssertionError) as e:p.exit(1,'FF16_SMALL_ENGINE_FAIL '+str(e)+'\n')
