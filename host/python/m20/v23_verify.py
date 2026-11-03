"""V2.3 actual XSIM evidence orchestration; never creates hardware event CSVs."""
import argparse,csv,hashlib,json,re,shutil,tempfile
from pathlib import Path
from .rtl_regression import ROOT,prepare,make_case,compare,TIMING_PROFILE
from .v2_verify import read_csv,DifferentialError,FIELDS
from .v23_audit import audit
from .v23_build import generate
PROFILES=('zero','delayed','reduced','max_delay','master_late','slave_early')

def checked(path, fresh=False):
 p=Path(path).resolve();base=ROOT/'build/m20_300/v23'
 if base not in p.parents:raise DifferentialError('output must be a NEW subdirectory of build/m20_300/v23')
 if fresh and p.exists():raise DifferentialError('refusing existing evidence directory; choose a new output')
 return p

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():
 paths=[]
 for folder in ('rtl/m20','sim/m20_v23'):
  paths += [p for p in (ROOT/folder).rglob('*') if p.is_file()]
 paths += list((ROOT/'host/python/m20').glob('*.py'))
 paths += [ROOT/'sim/scripts/run_m20_v23.sh',ROOT/'docs/m20/isa_v0_1.json']
 paths += list((ROOT/'software/m20_300').glob('*.asm'))
 paths += list((ROOT/'software/m20_300/reference').rglob('*'))
 return {str(p.relative_to(ROOT)):sha(p) for p in sorted(paths) if p.is_file() and '__pycache__' not in p.parts}
def inputs(output):
 return {str(p.relative_to(output)):sha(p) for p in sorted(output.rglob('*')) if p.is_file() and
   (p.name in ('cases.txt','metadata.json') or p.name.endswith(('.rom.memh','.ram.memh','.keys.txt','.expected.jsonl','.expected_ram.memh')))}

def pressure(directory):
 rows=[];lines=[]
 # Directed, independently interpreted launch vectors from the V2.2 short-path risks.
 specs=[('pc0_pc1',[0x0008,0xf100],dict(entry=1)),
        ('ar0_ar1',[0xa600,0xf100],dict(initial=dict(ar=1))),
        ('a0_c',[0x7100,0xf100],dict(initial=dict(a=1,c=0))),
        ('a3_c',[0x3001,0xf100],dict(initial=dict(a=8,c=0))),
        ('fsm_memory',[0x0005,0x8122,0x8022,0xf100],{})]
 # PC1 must execute LDI at address1 and increment binary01 ->10.
 specs[0]=('pc0_pc1',[0xf000,0x0008,0xf100],dict(entry=1))
 for name,words,kw in specs:
  row,line=make_case(directory,name,words,kind='short_path_pressure',**kw);rows.append(row);lines.append(line)
 (directory/'cases.txt').write_text('\n'.join(lines)+'\n')
 (directory/'metadata.json').write_text(json.dumps(dict(suite='pressure',isa_id='M20-300-ISA-0.1',timing_profile=TIMING_PROFILE,cases=rows),indent=2)+'\n')

def prepare_all(path):
 out=checked(path,True);out.mkdir(parents=True)
 for profile in PROFILES:
  if profile in ('zero','delayed'):prepare(out/profile)
  pressure(out/profile/'pressure')
 # Regenerate elsewhere, then compare bytes. Never overwrite formal generated source.
 with tempfile.TemporaryDirectory(prefix='v23-regenerate-',dir=out) as tmp:
  generate(Path(tmp))
  for p in Path(tmp).iterdir():
   if p.read_bytes()!=(ROOT/'rtl/m20/v23/generated'/p.name).read_bytes():raise DifferentialError('generated source not reproducible')
 (out/'resource_audit.json').write_text(json.dumps(audit(ROOT/'rtl/m20/v23/generated'),indent=2)+'\n')
 (out/'source_sha256.json').write_text(json.dumps(sources(),indent=2)+'\n')
 (out/'input_sha256.json').write_text(json.dumps(inputs(out),indent=2)+'\n')
 print('M20V23_PREPARED frozen87 cases x zero/delayed;5 directed pressure cases x6 profiles')

def compare_four(path):
 d=checked(path);compare(d);meta=json.loads((d/'metadata.json').read_text());events=0
 for case in meta['cases']:
  name=case['name'];gold=read_csv(d/f'{name}.rtl.csv')
  ram=(d/f'{name}.ram.final.memh').read_text().split()
  for suffix in ('v1','ideal','switch'):
   other=read_csv(d/f'{name}.{suffix}.csv')
   if gold!=other:raise DifferentialError(f'{name}: {suffix} independent RTL events differ')
   if ram!=(d/f'{name}.{suffix}.ram.final.memh').read_text().split():raise DifferentialError(f'{name}: {suffix} RAM differs')
  events+=len(gold)
 result=dict(status='PASS',cases=len(meta['cases']),events=events,suite=meta['suite'],
  participants=['Python ISA','V1 behavior','V2.1 IDEAL_FF','V2.3 TWO_PHASE_LATCH','V2.3 IDEAL_FF'])
 (d/'four_rtl_python_comparison.json').write_text(json.dumps(result,indent=2)+'\n')
 print(f'M20V23_FOUR_RTL_PYTHON_PASS suite={meta["suite"]} cases={len(meta["cases"])} events={events}')
 return result

def summarize(path):
 out=checked(path)
 if sources()!=json.loads((out/'source_sha256.json').read_text()):raise DifferentialError('sources changed DURING regression')
 if inputs(out)!=json.loads((out/'input_sha256.json').read_text()):raise DifferentialError('original expected fixtures changed DURING regression')
 results=[]
 for profile in PROFILES:
  suites=('instructions','games','pressure') if profile in ('zero','delayed') else ('pressure',)
  for suite in suites:
   r=json.loads((out/profile/suite/'four_rtl_python_comparison.json').read_text())
   text=(out/profile/'xsim'/f'{suite}.log').read_text()
   m=re.search(r'M20V23_CPU_PASS cases=(\d+) microcycles=(\d+)',text)
   if r['status']!='PASS' or not m or int(m[1])!=r['cases']:raise DifferentialError('missing actual completion')
   if suite=='instructions' and (r['cases'],r['events'])!=(49,22223):raise DifferentialError('instruction baseline changed')
   if suite=='games' and (r['cases'],r['events'])!=(38,35108):raise DifferentialError('game baseline changed')
   results.append(dict(profile=profile,suite=suite,status='PASS',cases=r['cases'],events=r['events'],microcycles=int(m[2])))
 required=[('zero','step','M20V23_STEP_PASS'),('zero','scheduler','M20V23_SCHEDULER_PASS'),('zero','penetration','M20V23_PENETRATION_PASS'),
  ('zero','memory','M20V23_MEMORY_PASS checks=7'),('delayed','memory','M20V23_MEMORY_PASS checks=7'),
  ('zero','illegal','M20V23_ILLEGAL_PASS words=65536 legal=15015 illegal=50521 actual_trap=50521 recovered=50521')]
 for profile,name,marker in required:
  if marker not in (out/profile/'xsim'/f'{name}.log').read_text():raise DifferentialError('missing '+marker)
 for label,marker in (('bad_ram','V23_RAM_RESPONSE_SETUP'),('bad_rom','V23_ROM_CHANGED_MASTER_OPEN')):
  if 'Fatal: '+marker not in (out/'zero/xsim'/f'{label}.log').read_text():raise DifferentialError('bad memory window not detected')
 neg=(out/'negative/xsim/overlap.log').read_text()
 if 'Fatal: V23_PHASE_OVERLAP' not in neg or 'M20V23_PENETRATION_PASS' in neg:raise DifferentialError('negative not detected')
 with (out/'regression_summary.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
 result=dict(status='PASS',timing_profile=TIMING_PROFILE,profiles=results,illegal_actual_terminal=50521,
  illegal_reset_recovery=50521,memory_checks_per_profile=7,resource_audit=json.loads((out/'resource_audit.json').read_text()),
  expected_overlap_negative='DETECTED',actual_penetration='DETECTED',limitations='Digital delay experiments only; not physical NC7SZ157 hold/setup signoff')
 (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
 print('M20V23_EVIDENCE_PASS baseline57331 events/profile zero+delayed;all50521illegal;memory7;negative detected')

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('prepare','compare','summarize'));p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 try:{'prepare':prepare_all,'compare':compare_four,'summarize':summarize}[a.command](a.output)
 except (OSError,ValueError,AssertionError) as e:p.exit(1,f'M20V23_VERIFY_FAIL: {e}\n')
if __name__=='__main__':main()
