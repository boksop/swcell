#!/usr/bin/env python3
"""Archive small V2.3 summaries and render actual traces; original evidence is read-only."""
import argparse,csv,hashlib,json,shutil
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
 with p.open() as f:return list(csv.DictReader(f))
def save_figure(fig,target):
 fig.savefig(target)
 if Path(target).suffix=='.svg':
  p=Path(target);p.write_text('\n'.join(line.rstrip() for line in p.read_text().splitlines())+'\n')
def plot_trace(source,target):
 r=rows(source)[:180];t0=float(r[0]['time_ns']);x=[float(v['time_ns'])-t0 for v in r]
 fig,axes=plt.subplots(5,1,sharex=True,figsize=(11,6),layout='constrained')
 for ax,key,label in zip(axes,('master_hold','slave_open','commit_ce','rom_read_ce','pc_hex'),('Master transparent','Slave open','Commit CE','ROM address sample','PC (word address)')):
  values=[int(v[key],16) for v in r]
  if key=='master_hold':values=[1-v for v in values]
  ax.step(x,values,where='post');ax.set_ylabel(label,fontsize=8);ax.grid(alpha=.3)
 axes[-1].set_xlabel('Time relative to first captured sys_clk edge (ns)')
 fig.suptitle('Actual XSIM trace: zero-delay CPU + synchronous BRAM (20 ns sampling)');save_figure(fig,target);plt.close(fig)
def plot_penetration(source,target):
 r=rows(source);r=[v for v in r if 115<=float(v['time_ns'])<=180]
 fig,axes=plt.subplots(5,1,sharex=True,figsize=(10,6),layout='constrained')
 for ax,key in zip(axes,('effective_master_hold','effective_slave_open','d','qm','q')):
  valid=[v for v in r if v[key] in ('0','1')]
  ax.step([float(v['time_ns']) for v in valid],[int(v[key]) for v in valid],where='post');ax.set_ylabel(key,fontsize=8);ax.set_ylim(-.15,1.15);ax.grid(alpha=.3)
  ax.axvspan(150.5,162.5,color='red',alpha=.12)
 axes[-1].set_xlabel('Actual simulation time (ns); red = both stages transparent')
 fig.suptitle('Negative witness: expected held Q=0, observed Q=1');save_figure(fig,target);plt.close(fig)
def archive(run,out):
 run=run.resolve();out=out.resolve()
 if run==out or out in run.parents:raise ValueError('destination cannot be run or its ancestor')
 result=json.loads((run/'verification.json').read_text())
 if result['status']!='PASS':raise ValueError('requires completed actual verification')
 if out.exists():raise ValueError('refusing existing archive destination')
 out.mkdir(parents=True)
 for name in ('verification.json','regression_summary.csv','resource_audit.json','source_sha256.json'):
  shutil.copyfile(run/name,out/name)
 for name,source in [('timing_trace.csv',run/'zero/instructions/timing_trace.csv'),('penetration.csv',run/'zero/xsim/penetration.csv'),('penetration.vcd',run/'zero/xsim/penetration.vcd')]:
  if source.exists():shutil.copyfile(source,out/name)
 plot_trace(out/'timing_trace.csv',out/'two_phase_trace.svg');plot_penetration(out/'penetration.csv',out/'overlap_penetration.svg')
 # Only selected raw evidence/logs, not XSIM library/cache binaries. Paths remain relative.
 manifest=[]
 for p in sorted(run.rglob('*')):
  if not p.is_file() or out in p.parents or 'xsim.dir' in p.parts or p.suffix not in ('.csv','.json','.jsonl','.memh','.txt','.log','.vcd','.wdb'):continue
  manifest.append(dict(path=str(p.relative_to(run)),bytes=p.stat().st_size,sha256=digest(p)))
 with (out/'evidence_sha256.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=('path','bytes','sha256'));w.writeheader();w.writerows(manifest)
 (out/'origin.json').write_text(json.dumps(dict(run_path=str(run),verification_sha256=digest(run/'verification.json'),indexed_files=len(manifest),indexed_bytes=sum(v['bytes'] for v in manifest),description='Actual local XSIM evidence; no physical hardware claims'),indent=2)+'\n')
 print(f'M20V23_ARCHIVE_PASS files={len(manifest)} output={out}')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();archive(a.run,a.output)
