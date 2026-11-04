#!/usr/bin/env python3
"""Archive actual A/B evidence and figures without changing raw results."""
import argparse,csv,hashlib,json,math,shutil,tarfile
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read_rows(p):
 with p.open() as f:return list(csv.DictReader(f))
def bit(value,index):
 try:return (int(value,16)>>index)&1
 except ValueError:return math.nan

def root_margins(trace):
 rows=read_rows(trace);groups={};previous=None
 for r in rows:
  if r['checking']=='1' and int(r['reference_cycle'])<4 and r['measurement_kind'] in ('1','2') and previous is not None:
   key=(r['measurement_kind'],r['reference_cycle']);v=groups.setdefault(key,dict(hr=[],hf=[],sr=[],sf=[]))
   for k,field,old,new in (('hr','master_hold','0','1'),('hf','master_hold','1','0'),('sr','slave_open','0','1'),('sf','slave_open','1','0')):
    if previous[field]==old and r[field]==new:v[k].append(float(r['time_ns']))
  previous=r
 results={}
 for direction in ('1','2'):
  values=[]
  for (kind,cycle),v in groups.items():
   if kind!=direction:continue
   closing=v['hr'] if direction=='1' else v['sf'];opening=v['sr'] if direction=='1' else v['hf']
   if len(closing)==len(opening)==1:values.append(opening[0]-closing[0])
  results['root_d'+direction+'_ns']=min(values) if values else None
  results['root_d'+direction+'_valid_cycles']=len(values)
 return results

def save(fig,p):
 fig.savefig(p);plt.close(fig)
 if p.suffix=='.svg':p.write_text('\n'.join(v.rstrip() for v in p.read_text().splitlines())+'\n')
def race_figure(trace,target,direction=1):
 rows=read_rows(trace);start=next(float(v['time_ns']) for v in rows if v['checking']=='1' and v['measurement_kind']==str(direction) and v['reference_cycle']=='0')
 selected=[v for v in rows if float(v['time_ns'])<=start+30]
 x=[float(v['time_ns'])-start for v in selected]
 if direction==1:
  signals=[('Root Master transparent',lambda r:1-int(r['master_hold'])),('Root Slave open',lambda r:int(r['slave_open'])),('Master32 transparent',lambda r:1-bit(r['master_effective'],32)),('Slave0 transparent',lambda r:bit(r['slave_effective'],0)),('Q0',lambda r:bit(r['q'],0)),('QM32',lambda r:bit(r['qm'],32)),('Q32 (expected 0)',lambda r:bit(r['q'],32))]
 else:
  signals=[('Master0 transparent',lambda r:1-bit(r['master_effective'],0)),('Slave0 transparent',lambda r:bit(r['slave_effective'],0)),('QM0',lambda r:bit(r['qm'],0)),('Q0 (expected hold 0)',lambda r:bit(r['q'],0))]
 overlap=[float(v['time_ns'])-start for v in selected if float(v['time_ns'])>=start and (1-bit(v['master_effective'],32 if direction==1 else 0))==1 and bit(v['slave_effective'],0)==1]
 begin=min(overlap);end=next(float(v['time_ns'])-start for v in selected if float(v['time_ns'])-start>begin and ((1-bit(v['master_effective'],32 if direction==1 else 0))==0 or bit(v['slave_effective'],0)==0))
 fig,axes=plt.subplots(len(signals),1,sharex=True,figsize=(10,1+len(signals)*.9),layout='constrained')
 for ax,(label,fn) in zip(axes,signals):
  ax.step(x,[fn(v) for v in selected],where='post');ax.axvspan(begin,end,color='red',alpha=.14);ax.set_ylabel(label,fontsize=8);ax.set_ylim(-.15,1.15);ax.grid(alpha=.25)
 axes[-1].set_xlim(-2,26);axes[-1].set_xlabel('Time from reference '+('rise' if direction==1 else 'fall')+' (ns); red = effective overlap')
 fig.suptitle('Actual XSIM: '+('cross-register race despite no own-bit overlap' if direction==1 else 'late Slave closing causes low-phase data penetration'))
 save(fig,target)
 return dict(reference_edge_ns=start,overlap_begin_relative_ns=begin,overlap_end_relative_ns=end)

def archive(run,dest):
 run=run.resolve();dest=dest.resolve()
 if dest.exists():raise ValueError('refusing existing archive')
 result=json.loads((run/'small_verification.json').read_text())
 if result['model_witness_status']!='VERIFIED':raise ValueError('missing model witnesses')
 dest.mkdir(parents=True)
 for name in ('small_verification.json','timing_results.csv','source_sha256.json','input_sha256.json'):
  shutil.copyfile(run/name,dest/name)
 for p in (run/'structure').iterdir():shutil.copyfile(p,dest/p.name)
 rows=result['results'];enriched=[]
 for r in rows:
  p=run/f'tap{r["tap"]}'/f'{r["case"]}_tap{r["tap"]}.trace.csv'
  enriched.append(dict(**r,**root_margins(p)))
 with (dest/'root_and_leaf_margins.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(enriched[0]));w.writeheader();w.writerows(enriched)
 fig,ax=plt.subplots(figsize=(9,4),layout='constrained')
 for name,key,label in [('nominal','d1_ns','nominal D1/D2'),('independent_cross','d1_ns','independent cross D1/D2'),('edge_asymmetric','d2_ns','asymmetric falling D2'),('fast_chain_sensitivity','d1_ns','unqualified fast chain D1/D2')]:
  a=[v for v in rows if v['case']==name];ax.plot([v['tap'] for v in a],[v[key] for v in a],marker='o',label=label)
 ax.axhline(0,color='red',label='overlap boundary');ax.axhline(4,color='gray',linestyle='--',label='assumed guard 4 ns');ax.set_xticks([4,8,12,16]);ax.set_xlabel('Selected tap (physical cells always 20)');ax.set_ylabel('Measured global effective margin (ns)');ax.grid(alpha=.3);ax.legend(fontsize=8);ax.set_title('Actual XSIM per-case assumptions; no physical minimum guarantee');save(fig,dest/'effective_margins.svg')
 cross=run/'tap4/independent_cross_tap4.trace.csv';negative=run/'tap4/slave_late_tap4.trace.csv'
 moments=race_figure(cross,dest/'cross_register_race.svg',1);race_figure(negative,dest/'fall_penetration.svg',2)
 for source in (cross,negative,run/'tap4/independent_cross_tap4.errors.csv'):
  shutil.copyfile(source,dest/source.name)
 cfg=json.loads((run/'tap4/independent_cross.json').read_text());failure=read_rows(run/'tap4/independent_cross_tap4.errors.csv')[0]
 snapshot=dict(classification='ACTUAL_TWO_DFF_SUBNETWORK_WITNESS_NOT_PROVEN_GLOBALLY_MINIMAL',tap=4,source_register=0,destination_register=32,comb_delay_ns=.1,old_source_q=0,old_destination_q=0,source_d_before_rise=1,expected_destination=0,actual_destination=1,
  actual_error_detection=failure,actual_overlap=moments,clock_gates=cfg['gates'],source_leaf=cfg['leaves'][0],destination_leaf=cfg['leaves'][32],all_parameter_source='assumed',q_qm_trace=str(cross.relative_to(run)))
 (dest/'minimal_cross_register_counterexample.json').write_text(json.dumps(snapshot,indent=2)+'\n')
 index=[]
 for p in sorted(run.rglob('*')):
  if p.is_file() and 'xsim.dir' not in p.parts and p.suffix in ('.csv','.json','.cfg','.txt','.log','.vcd','.wdb'):
   index.append(dict(path=str(p.relative_to(run)),bytes=p.stat().st_size,sha256=sha(p)))
 with (dest/'evidence_sha256.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=('path','bytes','sha256'));w.writeheader();w.writerows(index)
 (dest/'origin.json').write_text(json.dumps(dict(run=str(run),indexed_files=len(index),indexed_bytes=sum(v['bytes'] for v in index),summary_sha256=sha(run/'small_verification.json'),project_gate=result['project_gate'],cpu_regression='NOT_RUN'),indent=2)+'\n')
 # Portable upload artifact outside the raw result directory, excluding all compile caches.
 bundle=run.parent/(run.name+'_evidence.tar.gz')
 if bundle.exists():raise ValueError('refusing existing upload bundle')
 with tarfile.open(bundle,'w:gz') as t:
  for v in index:t.add(run/v['path'],arcname='raw/'+v['path'],recursive=False)
  for p in sorted(dest.iterdir()):t.add(p,arcname='report/'+p.name,recursive=False)
 (dest/'upload_bundle.json').write_text(json.dumps(dict(path=str(bundle),bytes=bundle.stat().st_size,sha256=sha(bundle),uploaded=False),indent=2)+'\n')
 print('FF16_EVIDENCE_ARCHIVED gate='+result['project_gate']+' files='+str(len(index)))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();archive(a.run,a.output)
