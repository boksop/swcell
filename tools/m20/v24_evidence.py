#!/usr/bin/env python3
"""Read existing V24 evidence; archive summaries and explicit post-review limitations."""
import argparse,csv,hashlib,json,shutil
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def archive(run,dest):
 run=run.resolve();dest=dest.resolve()
 if dest.exists():raise ValueError('new archive destination required')
 if json.loads((run/'verification.json').read_text())['status']!='PASS':raise ValueError('configured simulation incomplete')
 dest.mkdir(parents=True)
 for name in ('verification.json','regression_summary.csv','resource_audit.json','source_sha256.json'):
  shutil.copyfile(run/name,dest/name)
 with (run/'B_timed/instructions/timing_trace.csv').open() as f:rows=list(csv.DictReader(f))[:160]
 with (dest/'timing_trace.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 x=[float(v['time_ns'])-float(rows[0]['time_ns']) for v in rows]
 fig,axes=plt.subplots(5,1,sharex=True,figsize=(11,6),layout='constrained')
 for ax,key,label in zip(axes,('master_hold','slave_open','ram_sample_ce','rom_read_ce','pc_hex'),('Master transparent','Slave open','RAM sample CE','ROM sample CE','PC (word)')):
  y=[int(v[key],16) for v in rows]
  if key=='master_hold':y=[1-v for v in y]
  ax.step(x,y,where='post');ax.set_ylabel(label,fontsize=8);ax.grid(alpha=.3)
 axes[-1].set_xlabel('Time relative to first captured falling reference edge (ns)')
 fig.suptitle('Actual V24 B_timed trace: opposite-edge common-reference service (1 us sampling)')
 svg=dest/'common_reference_service.svg';fig.savefig(svg);plt.close(fig);svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
 index=[]
 for p in sorted(run.rglob('*')):
  if p.is_file() and 'xsim.dir' not in p.parts and p.suffix in ('.csv','.json','.jsonl','.memh','.log','.txt','.wdb'):
   index.append(dict(path=str(p.relative_to(run)),bytes=p.stat().st_size,sha256=sha(p)))
 with (dest/'evidence_sha256.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=('path','bytes','sha256'));w.writeheader();w.writerows(index)
 (dest/'origin.json').write_text(json.dumps(dict(run=str(run),files=len(index),bytes=sum(v['bytes'] for v in index),verification_sha256=sha(run/'verification.json')),indent=2)+'\n')
 (dest/'review_status.json').write_text(json.dumps(dict(project_status='NEEDS_ARCHITECTURE_REVIEW',configured_simulation='PASS',blocker='Master and Slave select arcs share one parameter; independent fast/slow crossing not covered. Local interlock source ordering does not imply effective latch ordering.',mixed_arc_counterexample='NOT_RUN: paused at theoretical review per user instruction',physical_signoff='NOT_DONE',v24_acceptance_tag='NOT_CREATED'),indent=2)+'\n')
 print('V24_EXISTING_EVIDENCE_ARCHIVED',len(index),'NOT_AN_ACCEPTANCE')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();archive(a.run,a.output)
