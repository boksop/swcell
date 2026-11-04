"""New V2.4 evidence, no overwrites of frozen V2.3 or Python expectations."""
import argparse,json,hashlib,csv,re,tempfile
from pathlib import Path
from .rtl_regression import ROOT,prepare,compare,DifferentialError
from .v2_verify import read_csv
from .v23_verify import pressure,inputs
from .v24_audit import audit
from .v24_build import generate
PROFILES=('A_zero','B_zero','C_zero','A_timed','B_timed','C_timed','B_slow')
def checked(p,fresh=False):
 p=Path(p).resolve();b=ROOT/'build/m20_300/v24'
 if b not in p.parents or (fresh and p.exists()):raise DifferentialError('requires NEW subdirectory of build/m20_300/v24')
 return p
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():
 paths=[]
 for d in ('rtl/m20','sim/m20_v24','sim/m20_v23'):
  paths += [p for p in (ROOT/d).rglob('*') if p.is_file()]
 paths+=list((ROOT/'host/python/m20').glob('*.py'))+list((ROOT/'host/python/tests').glob('test_m20*.py'))
 paths += [ROOT/p for p in ('sim/scripts/run_m20_v24.sh','sim/scripts/run_m20_v24_unit.sh','docs/m20/isa_v0_1.json')]
 paths+=list((ROOT/'software/m20_300').glob('*.asm'))
 return {str(p.relative_to(ROOT)):sha(p) for p in sorted(set(paths)) if '__pycache__' not in p.parts}
def prepare_all(path):
 out=checked(path,True);out.mkdir(parents=True)
 for profile in PROFILES:
  if profile!='B_slow':prepare(out/profile)
  pressure(out/profile/'pressure')
 with tempfile.TemporaryDirectory(prefix='reproduce-',dir=out) as t:
  generate(Path(t))
  for p in Path(t).iterdir():
   if p.read_bytes()!=(ROOT/'rtl/m20/v24/generated'/p.name).read_bytes():raise DifferentialError('generator not reproducible')
 (out/'resource_audit.json').write_text(json.dumps(audit(ROOT/'rtl/m20/v24/generated'),indent=2)+'\n')
 (out/'source_sha256.json').write_text(json.dumps(sources(),indent=2)+'\n')
 (out/'input_sha256.json').write_text(json.dumps(inputs(out),indent=2)+'\n')
def compare_all(path):
 d=checked(path);compare(d);m=json.loads((d/'metadata.json').read_text());n=0
 for c in m['cases']:
  name=c['name'];gold=read_csv(d/f'{name}.rtl.csv');ram=(d/f'{name}.ram.final.memh').read_text().split()
  for other in ('v1','ideal','switch'):
   if gold!=read_csv(d/f'{name}.{other}.csv'):raise DifferentialError(name+' independent RTL mismatch '+other)
   if ram!=(d/f'{name}.{other}.ram.final.memh').read_text().split():raise DifferentialError(name+' independent RAM mismatch '+other)
  n+=len(gold)
 r=dict(status='PASS',suite=m['suite'],cases=len(m['cases']),events=n)
 (d/'all_comparison.json').write_text(json.dumps(r,indent=2)+'\n');print('V24_FOUR_RTL_PYTHON_PASS',r)
def summarize(path):
 out=checked(path)
 if sources()!=json.loads((out/'source_sha256.json').read_text()):raise DifferentialError('sources changed during verification')
 if inputs(out)!=json.loads((out/'input_sha256.json').read_text()):raise DifferentialError('fixtures changed during verification')
 rows=[]
 for profile in PROFILES:
  for suite in (('pressure',) if profile=='B_slow' else ('instructions','games','pressure')):
   r=json.loads((out/profile/suite/'all_comparison.json').read_text());log=(out/profile/'xsim'/f'{suite}.log').read_text()
   if 'M20V24_CPU_PASS' not in log or r['status']!='PASS':raise DifferentialError('missing actual completion')
   if suite=='instructions' and (r['cases'],r['events'])!=(49,22223):raise DifferentialError('original instruction cases changed')
   if suite=='games' and (r['cases'],r['events'])!=(38,35108):raise DifferentialError('original games changed')
   rows.append(dict(profile=profile,**r))
  if profile!='B_slow' and 'M20V24_MEMORY_PASS checks=7' not in (out/profile/'xsim/memory.log').read_text():raise DifferentialError('memory regression incomplete')
 for p in ('nominal','fast','slow'):
  if 'illegal_recovered=8' not in (out/'unit'/p/'run.log').read_text():raise DifferentialError('unit incomplete')
 if 'Fatal: V23_PHASE_OVERLAP' not in (out/'unit/bad_skew/run.log').read_text():raise DifferentialError('negative not caught')
 if 'M20V24_ILLEGAL_PASS words=65536 legal=15015 illegal=50521 actual_trap=50521 recovered=50521' not in (out/'B_timed/xsim/illegal.log').read_text():raise DifferentialError('illegal terminals incomplete')
 with (out/'regression_summary.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 result=dict(status='PASS',classification='DIGITAL_BOUNDED_DELAY_COSIM_NOT_PHYSICAL_SIGNOFF',frozen_v23_commit='aecf570c2e33563179e95e1615fd005cc19817f5',profiles=rows,illegal_terminals=50521,illegal_reset_recoveries=50521,memory_cases_per_full_profile=7,unit_delay_profiles=3,local_skew_negative='DETECTED',generator_mux=116,cpu_mux=543,system_mux_excluding_buffers=659,interface='Common selected CLK_REF, opposite-edge FPGA phase feedback/BRAM service; D1 write event')
 (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('M20_V24_EVIDENCE_PASS')
def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=('prepare','compare','summarize'));p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 try:{'prepare':prepare_all,'compare':compare_all,'summarize':summarize}[a.command](a.output)
 except (OSError,ValueError,AssertionError) as e:p.exit(1,'V24_FAIL '+str(e)+'\n')
if __name__=='__main__':main()
