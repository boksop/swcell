"""Prepare unchanged V1 scenarios and validate actual V0/V1/V2 XSIM evidence.

Only SystemVerilog testbenches write RTL CSVs; this module never manufactures
hardware results or modifies the immutable V1 evidence directory.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re

from .rtl_regression import prepare, compare, FIELDS, DifferentialError, ROOT

VARIANTS=('baseline','shared')


def checked_output(path):
    output=Path(path).resolve()
    original=ROOT/'build/m20_300/v1'
    if output==original or original in output.parents:
        raise DifferentialError('V2 must not overwrite original V1 evidence')
    return output


def fingerprints():
    # Fixed V1 manifest, rather than globbing all future host/m20 additions.
    prior=json.loads((ROOT/'build/m20_300/v1/inputs_manifest.json').read_text())
    paths=[ROOT/path for path in prior]
    for directory in (ROOT/'rtl/m20/v2',ROOT/'sim/m20_v2'):
        paths += [p for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths += [ROOT/'host/python/m20/v2_verify.py',ROOT/'sim/scripts/run_m20_v2.sh']
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(set(paths))}


def prepare_all(path):
    output=checked_output(path)
    output.mkdir(parents=True,exist_ok=True)
    for variant in VARIANTS:
        prepare(output/variant)
    (output/'v2_sources_before.json').write_text(json.dumps(fingerprints(),indent=2)+'\n')
    (output/'v2_inputs_before.json').write_text(json.dumps(input_fingerprints(output),indent=2)+'\n')
    print('M20V2_PREPARED immutable 49 instruction / 38 game scenarios per variant')
    return 0


def read_csv(path):
    with path.open() as stream:
        reader=csv.DictReader(stream)
        if tuple(reader.fieldnames or ())!=FIELDS:
            raise DifferentialError(f'{path}: bad CSV fields')
        try:return [{key:int(value) for key,value in row.items()} for row in reader]
        except (ValueError,TypeError) as error:
            raise DifferentialError(f'{path}: malformed/nonnumeric V1 CSV: {error}') from error


def input_fingerprints(output):
    paths=[]
    for variant in VARIANTS:
        paths.append(output/variant/'inputs_manifest.json')
        for suite in ('instructions','games'):
            directory=output/variant/suite
            paths.extend([directory/'metadata.json',directory/'cases.txt'])
            metadata=json.loads((directory/'metadata.json').read_text())
            for case in metadata['cases']:
                paths.extend(directory/f'{case["name"]}.{suffix}' for suffix in
                    ('rom.memh','ram.memh','keys.txt','expected.jsonl','expected_ram.memh'))
    return {str(path.relative_to(output)):hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)}


def compare_three(directory):
    directory=checked_output(directory)
    compare(directory)  # Independent Python interpreter versus V2 CSV/final RAM.
    metadata=json.loads((directory/'metadata.json').read_text())
    events=0
    for case in metadata['cases']:
        name=case['name']
        v1=read_csv(directory/f'{name}.v1.csv')
        v2=read_csv(directory/f'{name}.rtl.csv')
        if len(v1)!=len(v2):raise DifferentialError(f'{name}: V1/V2 event count mismatch')
        for index,(left,right) in enumerate(zip(v1,v2)):
            fields=[field for field in FIELDS if field not in ('ram_addr','ram_data') or left['ram_kind']]
            if any(left[field]!=right[field] for field in fields):
                failure=dict(test=name,instruction_index=index,v1=left,v2=right)
                (directory/'v1_v2_first_mismatch.json').write_text(json.dumps(failure,indent=2)+'\n')
                raise DifferentialError(f'{name}: V1/V2 mismatch at event {index}')
        left=[int(word,16) for word in (directory/f'{name}.v1.ram.final.memh').read_text().split()]
        right=[int(word,16) for word in (directory/f'{name}.ram.final.memh').read_text().split()]
        if len(left)!=256 or left!=right:raise DifferentialError(f'{name}: V1/V2 final RAM mismatch')
        events+=len(v2)
    result=dict(status='PASS',case_count=len(metadata['cases']),events=events,
        evidence='Independent V1/V2 XSIM CSVs and final RAM agree; V2 also matches V0 Python')
    (directory/'three_way_comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'M20V2_THREE_WAY_PASS {metadata["suite"]} cases={result["case_count"]} events={events}')
    return 0


def summarize(path):
    output=checked_output(path)
    sources=json.loads((output/'v2_sources_before.json').read_text())
    if sources!=fingerprints():raise DifferentialError('V2 sources changed during simulation')
    input_hashes=json.loads((output/'v2_inputs_before.json').read_text())
    if input_hashes!=input_fingerprints(output):raise DifferentialError('V2 fixtures/expected events changed during simulation')
    variants={}
    for variant in VARIANTS:
        base=output/variant
        xsim=base/'xsim'
        required={
            'mux':'SWC_MUX157_PASS vectors=8',
            'isa':'M20V2_ISA_PASS words=65536 legal=15015 illegal=50521 alu_vectors=32768',
            'memory':'M20V2_MEMORY_PASS checks=7 ',
        }
        for label,sentinel in required.items():
            if sentinel not in (xsim/f'{label}.log').read_text():
                raise DifferentialError(f'{variant}: missing actual {label} unit success')
        suites={}
        for suite in ('instructions','games'):
            result=json.loads((base/suite/'three_way_comparison.json').read_text())
            if result['status']!='PASS':raise DifferentialError(f'{variant}/{suite}: incomplete comparison')
            expected_events=22223 if suite=='instructions' else 35108
            if result['events']!=expected_events:raise DifferentialError('original V1 event count changed')
            text=(xsim/f'{suite}.log').read_text()
            match=re.search(r'M20V2_CPU_PASS cases=(\d+) lockstep_cycles=(\d+)',text)
            if not match or int(match.group(1))!=result['case_count']:
                raise DifferentialError(f'{variant}/{suite}: missing V1/V2 cycle lockstep completion')
            suites[suite]=result | dict(lockstep_cycles=int(match.group(2)))
        if suites['instructions']['case_count']!=49 or suites['games']['case_count']!=38:
            raise DifferentialError('original V1 scenario counts changed')
        variants[variant]=dict(status='PASS',suites=suites,exhaustive_decoder_words=65536,
            exhaustive_alu_vectors=32768,memory_checks=7,mux_vectors=8)
    result=dict(status='PASS',isa_id='M20-300-ISA-0.1',timing_profile='M20-300-V1-TIMING-0.1',
        variants=variants,source_fingerprints=sources,
        input_fingerprints=input_hashes,
        evidence='Actual XSIM V2 CSV + independent V1 CSV + independent Python events/final RAM',
        limits='Digital functional equivalence only, not physical 157 timing or exact gate-count audit')
    (output/'v2_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print('M20V2_EVIDENCE_PASS variants=2 cases_each=87 events_each=57331')
    return 0


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    for name in ('prepare','summarize'):
        sub=commands.add_parser(name);sub.add_argument('--output',type=Path,required=True)
    sub=commands.add_parser('compare');sub.add_argument('--directory',type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        if args.command=='prepare':return prepare_all(args.output)
        if args.command=='compare':return compare_three(args.directory)
        return summarize(args.output)
    except (OSError,ValueError,AssertionError) as error:
        parser.exit(1,f'M20V2_VERIFY_FAIL: {error}\n')


if __name__=='__main__':raise SystemExit(main())
