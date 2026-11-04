"""Actual feedforward C/D regression orchestration, separate from physical signoff."""
import argparse,csv,hashlib,json,re,shutil,tempfile
from pathlib import Path
from .rtl_regression import ROOT,prepare,make_case,compare,DifferentialError
from .v23_verify import pressure,inputs
from . import assemble
from .ffcd_audit import audit
PROFILES=('A_logic','A_timed','B_logic','B_timed','C_logic','C_timed')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def checked(path,fresh=False):
 p=Path(path).resolve();base=ROOT/'build/m20_300/v24_ffcd'
 if base not in p.parents or (fresh and p.exists()):raise DifferentialError('requires fresh child of build/m20_300/v24_ffcd')
 return p
def read(p):
 with Path(p).open() as f:return list(csv.DictReader(f))
def source_hashes():
 paths=[]
 for folder in ('rtl/m20','sim/m20_ffcd','sim/m20_v23','sim/m20_ff16'):
  paths += [p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
 paths+=list((ROOT/'host/python/m20').glob('*.py'))+[ROOT/'sim/scripts/run_m20_ffcd.sh',ROOT/'docs/m20/isa_v0_1.json']
 return {str(p.relative_to(ROOT)):sha(p) for p in sorted(set(paths))}
def prepare_all(path):
 out=checked(path,True);out.mkdir(parents=True)
 master=out/'fixtures';prepare(master);pressure(master/'pressure')
 specs=[('smoke_arithmetic_branch_memory',assemble('''LDI 5
ADDI 3
ST 0x22
LD 0x22
SUBI 8
JZ good
.word 0xffff
good: OUT
HALT''').words),('smoke_trap',[0xffff])]
 rows=[];lines=[]
 for name,words in specs:
  row,line=make_case(master/'smoke',name,words,kind='minimal_system');rows.append(row);lines.append(line)
 (master/'smoke/cases.txt').write_text('\n'.join(lines)+'\n')
 meta=json.loads((master/'pressure/metadata.json').read_text());meta.update(suite='smoke',cases=rows);(master/'smoke/metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
 for profile in PROFILES:
  shutil.copytree(master,out/profile)
 (out/'resource_audit.json').write_text(json.dumps(audit(),indent=2)+'\n')
 (out/'source_sha256.json').write_text(json.dumps(source_hashes(),indent=2)+'\n')
 (out/'input_sha256.json').write_text(json.dumps(inputs(out),indent=2)+'\n')
 print('FFCD_PREPARED unchanged87 per profile; C memory/control first; conditional digital only')
def compare_suite(path):
 d=checked(path);compare(d);meta=json.loads((d/'metadata.json').read_text());n=0
 for case in meta['cases']:
  name=case['name'];gold=read(d/f'{name}.rtl.csv');ram=(d/f'{name}.ram.final.memh').read_text().split()
  for other in ('v1','ideal','switch'):
   if gold!=read(d/f'{name}.{other}.csv'):raise DifferentialError(name+' RTL mismatch '+other)
   if ram!=(d/f'{name}.{other}.ram.final.memh').read_text().split():raise DifferentialError(name+' RAM mismatch '+other)
  n+=len(gold)
 r=dict(status='PASS',suite=meta['suite'],cases=len(meta['cases']),events=n)
 (d/'all_comparison.json').write_text(json.dumps(r,indent=2)+'\n');print('FFCD_RTL_PYTHON_PASS',r)
def summarize(path):
 out=checked(path)
 if source_hashes()!=json.loads((out/'source_sha256.json').read_text()):raise DifferentialError('sources changed during regression')
 if inputs(out)!=json.loads((out/'input_sha256.json').read_text()):raise DifferentialError('original input/expected data changed')
 records=[]
 for profile in PROFILES:
  for suite in ('instructions','games','pressure','smoke'):
   result=json.loads((out/profile/suite/'all_comparison.json').read_text())
   if suite=='instructions':assert (result['cases'],result['events'])==(49,22223)
   if suite=='games':assert (result['cases'],result['events'])==(38,35108)
   records.append(dict(profile=profile,**result))
  prefix='M20V23' if profile.startswith('A') else 'M20FFCD'
  assert prefix+'_MEMORY_PASS checks=7' in (out/profile/'xsim/memory.log').read_text()
 for suite in ('instructions','games','pressure','smoke'):
  golden=out/'A_logic'/suite;meta=json.loads((golden/'metadata.json').read_text())
  gm=read(golden/'microstates.csv')
  for profile in PROFILES[1:]:
   candidate=out/profile/suite
   assert gm==read(candidate/'microstates.csv'),('cross-mode microstates',profile,suite)
   for case in meta['cases']:
    name=case['name'];assert read(golden/f'{name}.rtl.csv')==read(candidate/f'{name}.rtl.csv'),('cross-mode retirement',profile,name)
    assert (golden/f'{name}.ram.final.memh').read_text().split()==(candidate/f'{name}.ram.final.memh').read_text().split()
 for profile in ('B_timed','C_timed'):
  assert 'M20FFCD_CONTROL_PASS' in (out/profile/'xsim/control.log').read_text()
  assert 'illegal=50521 actual_trap=50521 recovered=50521' in (out/profile/'xsim/illegal.log').read_text()
 with (out/'regression_summary.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
 result=dict(status='PASS',classification='CONDITIONAL_DIGITAL_SYSTEM_VERIFIED_NOT_PHYSICAL_SIGNOFF',profiles=records,
             participants=['Python ISA','V1 behavior','V21 IDEAL_FF','frozen V23 ModeA','feedforward ModeB','feedforward ModeC'],
             cpu_comb=477,cpu_storage=66,generator=20,total_excluding_buffers=563,isa_timing='M20-300-V1-TIMING-0.1',
             physical_minimum_delay='OPEN_NOT_A_DIGITAL_REGRESSION_GATE',historical_negatives='PRESERVED')
 (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('FFCD_SYSTEM_DIGITAL_VERIFIED physical_timing=NOT_VERIFIED')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','compare','summarize']);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 try:{'prepare':prepare_all,'compare':compare_suite,'summarize':summarize}[a.command](a.output)
 except (OSError,ValueError,AssertionError) as e:p.exit(1,'FFCD_FAIL '+str(e)+'\n')
