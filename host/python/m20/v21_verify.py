"""V2.1 evidence orchestration: only real XSIM writes CPU results."""
import argparse,hashlib,json,re
from pathlib import Path
from .rtl_regression import prepare as prepare_v1,ROOT,DifferentialError
from .v2_verify import compare_three

def checked(path):
    p=Path(path).resolve()
    for old in (ROOT/'build/m20_300/v1',ROOT/'build/m20_300/v2',ROOT/'build/m20_300/candidate_review_20261102'):
        if p==old or old in p.parents:raise DifferentialError('refusing historical evidence path')
    return p

def sources():
    old=json.loads((ROOT/'build/m20_300/v1/inputs_manifest.json').read_text())
    paths=[ROOT/p for p in old]
    for d in ('rtl/m20/v21','sim/m20_v21'):
        paths += [p for p in (ROOT/d).rglob('*') if p.is_file()]
    paths += [ROOT/f'host/python/m20/v21_{x}.py' for x in ('build','audit','verify')]
    paths += [ROOT/'sim/scripts/run_m20_v21.sh']
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))}

def inputs(output):
    return {str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()
            for suite in ('instructions','games') for p in sorted((output/suite).iterdir())
            if p.name in ('metadata.json','cases.txt') or p.name.endswith(('.rom.memh','.ram.memh','.keys.txt','.expected.jsonl','.expected_ram.memh'))}

def prepare(output):
    output=checked(output)
    if (output/'verification.json').exists():raise DifferentialError('choose new output to retain prior result')
    prepare_v1(output)
    (output/'sources_before.json').write_text(json.dumps(sources(),indent=2)+'\n')
    (output/'inputs_before.json').write_text(json.dumps(inputs(output),indent=2)+'\n')

def summarize(output):
    output=checked(output)
    if sources()!=json.loads((output/'sources_before.json').read_text()):raise DifferentialError('sources changed during run')
    if inputs(output)!=json.loads((output/'inputs_before.json').read_text()):raise DifferentialError('fixtures changed during run')
    required={'illegal':'M20V21_ILLEGAL_PASS words=65536 legal=15015 illegal=50521 recovery=50521',
              'datapath':'M20V21_DATAPATH_PASS math_vectors=27840 xz_probes=3',
              'memory':'M20V21_MEMORY_PASS checks=7', 'isa_v1':'M20_ISA_PASS'}
    for label,marker in required.items():
        if marker not in (output/'xsim'/f'{label}.log').read_text():raise DifferentialError(f'missing {label} completion')
    suites={}
    for s,count,event in [('instructions',49,22223),('games',38,35108)]:
        j=json.loads((output/s/'three_way_comparison.json').read_text())
        if (j['status'],j['case_count'],j['events'])!=('PASS',count,event):raise DifferentialError('suite totals')
        if f'M20V21_CPU_PASS cases={count}' not in (output/'xsim'/f'{s}.log').read_text():raise DifferentialError('missing CPU completion')
        suites[s]=j
    result=dict(status='PASS',isa='M20-300-ISA-0.1',timing_profile='M20-300-V1-TIMING-0.1',suites=suites,
                illegal_words_actual_trap=50521,reset_recoveries=50521,legal_codes=15015,datapath_math_vectors=27840,
                xz_observation_probes=3,memory_checks=7,source_fingerprints=sources(),input_fingerprints=inputs(output),
                evidence='Actual V1/V2.1 XSIM per-cycle lockstep/CSV/final RAM and independent Python',
                limits='Not formal all-state equivalence or real 157 timing validation')
    (output/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('M20V21_EVIDENCE_PASS cases=87 events=57331 illegal=50521')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['prepare','compare','summarize']);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=checked(a.output)
    if a.command=='prepare':prepare(out)
    elif a.command=='compare':compare_three(out)
    else:summarize(out)
if __name__=='__main__':main()
