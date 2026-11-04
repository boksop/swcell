#!/usr/bin/env python3
"""Archive real full-system outputs, timing plots, and retained negative results."""
import argparse,csv,hashlib,json,re,shutil,tarfile
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]
PROFILES=('A_logic','A_timed','B_logic','B_timed','C_logic','C_timed')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def read(p):
 with p.open(newline='') as f:return list(csv.DictReader(f))
def write(p,rows):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

def vcd(path,wanted):
 scopes=[];ids={};events={k:[] for k in wanted};time=0;scale=.001
 with path.open() as f:
  header=True
  for line in f:
   s=line.strip()
   if header:
    if s.startswith('$scope'):scopes.append(s.split()[2])
    elif s.startswith('$upscope'):scopes.pop()
    elif s.startswith('$var'):
     a=s.split();name='/'.join(scopes+[a[4]])
     if name in wanted:ids.setdefault(a[3],[]).append(name)
    elif s.startswith('$enddefinitions'):header=False
   elif s.startswith('#'):time=int(s[1:])*scale
   elif s.startswith(('b','B')):
    a=s[1:].split()
    if len(a)==2 and a[1] in ids:
     val=None if re.search('[xXzZ]',a[0]) else int(a[0],2)
     for key in ids[a[1]]:events[key].append((time,val))
   elif s and s[0] in '01xXzZ' and s[1:] in ids:
    val=int(s[0]) if s[0] in '01' else None
    for key in ids[s[1:]]:events[key].append((time,val))
 assert all(events.values()),'missing VCD signal'
 return events

def timing(run,out):
 latency=[]
 base='tb_m20ffcd_memory/'
 for profile in ('B_timed','C_timed'):
  d=run/profile/'xsim';signals=[base+k for k in ('clk_ref','master_hold','slave_open','dut/state_me','dut/state_se')]
  wave=vcd(d/'memory_service.vcd',signals);edges=wave[base+'clk_ref'];table=read(d/'service_events.csv')
  for field,level in [('ram_sample',0),('preview',0),('write',1),('observe',1),('rom_read',1)]:
   delays=[]
   for row in table:
    if row[field]=='1':
     t=float(row['time_ns']);edge=max(tm for tm,v in edges if v==level and tm<=t)
     delays.append(t-edge)
   latency.append(dict(profile=profile,event=field,samples=len(delays),min_from_true_ref_edge_ns=min(delays),max_from_true_ref_edge_ns=max(delays),source='actual_VCD_reference_and_preNBA_service_event_CSV'))
  if profile=='B_timed':
   hit=next(row for row in table if row['write']=='1' and row['pending_write']=='1')
   commit=float(hit['time_ns']);rise=max(tm for tm,v in edges if v==1 and tm<=commit);origin=max(tm for tm,v in edges if v==0 and tm<rise)
   lo=origin-70;hi=origin+900
   lines=[('CLK_REF',wave[base+'clk_ref'],None),('Master32 transparent',wave[base+'dut/state_me'],lambda v:1-(v>>32&1)),('Slave0 transparent',wave[base+'dut/state_se'],lambda v:v&1),('Root H',wave[base+'master_hold'],None),('Root S',wave[base+'slave_open'],None)]
   fig,axes=plt.subplots(6,1,sharex=True,figsize=(11,7),layout='constrained')
   cropped=[]
   for ax,(label,data,fn) in zip(axes,lines):
    selected=[(t,val) for t,val in data if t<=hi]
    held=selected+[(hi,selected[-1][1])]
    ax.step([t-origin for t,val in held],[(float('nan') if val is None else fn(val) if fn else val) for t,val in held],where='post');ax.set_ylabel(label.replace(' transparent','\ntransparent'),fontsize=8,rotation=0,labelpad=42);ax.set_ylim(-.15,1.15);ax.grid(alpha=.2)
    for t,val in selected:
     if t>=lo:cropped.append(dict(signal=label,time_relative_ns=t-origin,value=None if val is None else fn(val) if fn else val))
   for n,field in enumerate(('ram_sample','preview','write','observe','rom_read')):
    x=[float(row['time_ns'])-origin for row in table if row[field]=='1' and lo<=float(row['time_ns'])<=hi]
    axes[-1].scatter(x,[n]*len(x),label=field,s=35);[axes[-1].annotate(field,(tm,n),xytext=(4,3),textcoords='offset points',fontsize=8) for tm in x]
   axes[-1].set_yticks([]);axes[-1].set_ylabel('FPGA events');axes[-1].set_xlabel('Time from actual reference falling edge (ns)')
   axes[-1].set_xlim(-70,900);fig.suptitle('Actual B_timed memory-service cycle; leaf D1/D2 = 22 ns (assumed model)')
   fig.savefig(out/'memory_service_timing.svg');plt.close(fig);write(out/'memory_wave_excerpt.csv',sorted(cropped,key=lambda v:v['time_relative_ns']))
 write(out/'service_latency.csv',latency)

def archive(run,out,negative_small,negative_cones,baseline_path=None):
 run=run.resolve();out=out.resolve()
 if out.exists():raise ValueError('refusing existing evidence output')
 verification=load(run/'verification.json');assert verification['status']=='PASS'
 assert all(sha(ROOT/p)==h for p,h in load(run/'source_sha256.json').items())
 out.mkdir(parents=True)
 for name in ('verification.json','resource_audit.json','regression_summary.csv','source_sha256.json','input_sha256.json'):shutil.copyfile(run/name,out/name)
 micro=[];tx=[];clocks=[]
 for profile in PROFILES:
  for suite in ('instructions','games','pressure','smoke'):
   d=run/profile/suite;metadata=load(d/'metadata.json');m=read(d/'microstates.csv');gold=run/'A_logic'/suite/'microstates.csv'
   assert m==read(gold)
   micro.append(dict(profile=profile,suite=suite,microstate_rows=len(m),state_values_include='PC_AR_A_Z_C_GPO_FSM_HALT_TRAP',matches_mode_a=True,sha256=sha(d/'microstates.csv')))
   log=(run/profile/'xsim'/f'{suite}.log').read_text()
   margins=re.search(r'FFCD_EFFECTIVE_MARGIN d1_ns=([\d.]+) d2_ns=([\d.]+) d1_checks=(\d+) d2_checks=(\d+)',log)
   if margins:
    assert (float(margins[1]),float(margins[2]))==(22.,22.)
    clocks.append(dict(profile=profile,suite=suite,d1_ns=margins[1],d2_ns=margins[2],rise_checks=margins[3],fall_checks=margins[4]))
   for case in metadata['cases']:
    name=case['name'];trace=read(d/f'{name}.rtl.csv');rd=sum(r['ram_kind']=='1' for r in trace);wr=sum(r['ram_kind']=='2' for r in trace)
    actual=re.search(r'CASE_PASS name='+re.escape(name)+r' events=(\d+) cycles=(\d+) writes=(\d+)',log)
    assert actual and rd==case['ram_reads'] and wr==case['ram_writes']==int(actual[3])
    tx.append(dict(profile=profile,suite=suite,case=name,logical_reads=rd,logical_writes=wr,persistent_writes=int(actual[3]),retired_event_rows=len(trace),physical_read_resampling='CE/OE spans3 states; repeated BRAM samples are not3 ISA transactions',final_ram_sha256=sha(d/f'{name}.ram.final.memh')))
 write(out/'microstate_comparison.csv',micro);write(out/'transactions.csv',tx);write(out/'effective_clocks.csv',clocks);timing(run,out)
 small=load(negative_small/'small_verification.json');cones=load(negative_cones/'cone_verification.json')
 assert (small['cases'],small['failed_cases'])==(56,24) and cones['fast_assumed_mismatches']==131
 negatives=dict(detection='VERIFIED',small_run=str(negative_small),small_result_sha256=sha(negative_small/'small_verification.json'),small_cases=56,small_conditional=32,small_FAILED_preserved=24,
                cones_run=str(negative_cones),cones_result_sha256=sha(negative_cones/'cone_verification.json'),cones_cases=632,cones_assumed_errors=131,
                service_bad_ram='V23_RAM_RESPONSE_SETUP',service_bad_rom='V23_ROM_CHANGED_MASTER_OPEN',physical_status='NOT_VERIFIED',note='negative configurations remain FAILED; only detection is verified')
 for name,marker in [('bad_ram','V23_RAM_RESPONSE_SETUP'),('bad_rom','V23_ROM_CHANGED_MASTER_OPEN')]:assert 'Fatal: '+marker in (run/f'B_timed/xsim/{name}.log').read_text()
 dump(out/'negative_replay.json',negatives)
 baseline=load(Path(baseline_path) if baseline_path else ROOT/'build/m20_300/v24_ffcd/baseline_20261104.json')
 assert all(sha(ROOT/p)==h for p,h in baseline['protected'].items())
 import subprocess
 assert subprocess.check_output(['git','ls-files','--stage','-z']).decode()==baseline['index']
 assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==baseline['head']
 assert subprocess.check_output(['git','rev-parse','m20-v2.3-two-phase-sim-verified^{}'],text=True).strip()==baseline['tag']
 py=(run/'python_tests.log').read_text();count=re.search(r'Ran (\d+) tests',py);assert count and '\nOK\n' in py and int(count[1])>=151
 validation=dict(status='VERIFIED_DIGITAL_NOT_PHYSICAL',python_tests=int(count[1]),python_log_sha256=sha(run/'python_tests.log'),
                 python_test_source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'host/python/tests').glob('test_*.py'))},
                 protected_existing_files=len(baseline['protected']),old_index_preserved=True,head=baseline['head'],v23_tag=baseline['tag'],digital_feature='PASS_UNDER_DECLARED_ASSUMPTIONS',physical='NOT_VERIFIED',git_commit_tag_remote_operations='NONE')
 dump(out/'validation.json',validation)
 index=[]
 for p in sorted(run.rglob('*')):
  if p.is_file() and 'xsim.dir' not in p.parts and out not in p.parents and p.suffix in ('.csv','.json','.log','.vcd','.memh','.txt','.jsonl'):
   index.append(dict(path=str(p.relative_to(run)),bytes=p.stat().st_size,sha256=sha(p)))
 write(out/'evidence_sha256.csv',index)
 dump(out/'origin.json',dict(run=str(run),indexed_files=len(index),indexed_bytes=sum(r['bytes'] for r in index),physical_status='NOT_VERIFIED',original_AB='unchanged',classification='bounded digital function; physical timing open'))
 bundle=run.with_name(run.name+'_evidence.tar.gz')
 if bundle.exists():raise ValueError('refusing bundle overwrite')
 with tarfile.open(bundle,'w:gz') as archive:
  for row in index:archive.add(run/row['path'],arcname='raw/'+row['path'],recursive=False)
  for p in sorted(out.iterdir()):archive.add(p,arcname='summary/'+p.name,recursive=False)
 dump(out/'bundle.json',dict(path=str(bundle),bytes=bundle.stat().st_size,sha256=sha(bundle),uploaded=False))
 print('FFCD_ARCHIVED_DIGITAL_VERIFIED files='+str(len(index)))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--negative-small',type=Path,required=True);p.add_argument('--negative-cones',type=Path,required=True);p.add_argument('--baseline',type=Path);a=p.parse_args();archive(a.run,a.output,a.negative_small.resolve(),a.negative_cones.resolve(),a.baseline)
