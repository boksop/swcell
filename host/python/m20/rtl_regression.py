"""Generate independent Python traces, then compare actual XSIM CPU events.

This program never creates simulated RTL results. Only the XSIM testbench writes
*.rtl.csv and *.ram.final.memh; missing or mismatched results are failures.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import random
import re

from . import Machine, assemble, encode
from .isa import ISA_VERSION
from .benchmarks import programs, pong_cases, snake_cases

ROOT = Path(__file__).resolve().parents[3]
TIMING_PROFILE = 'M20-300-V1-TIMING-0.1'
FIELDS = ('sequence','pc','word','next_pc','a','ar','z','c','gpo',
          'ram_kind','ram_addr','ram_data','cycles','cumulative_cycles',
          'event','halted','trapped')
INITIAL = dict(a=0,ar=0,z=1,c=0,gpo=8)


def source_fingerprints():
    paths=(list((ROOT/'rtl/m20').glob('*.sv'))+list((ROOT/'sim/m20').glob('*'))+
           list((ROOT/'host/python/m20').glob('*.py'))+
           list((ROOT/'host/python/tests').glob('test_m20*.py'))+
           list((ROOT/'software/m20_300').glob('*.asm'))+
           [ROOT/'sim/scripts/run_m20.sh',ROOT/'docs/m20/isa_v0_1.json',
            ROOT/'docs/m20/M20_300_ISA_FROZEN.md',ROOT/'docs/m20/M20_300_architecture_v0_1.md'])
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths) if p.is_file()}


def observed(event, sequence, machine):
    tx=event['ram_transaction']
    return dict(sequence=sequence,pc=event['pc'],word=event['word'],
        next_pc=event['next_pc'],a=event['a'],ar=event['ar'],z=event['z'],c=event['c'],gpo=event['gpo'],
        ram_kind=0 if tx is None else 2 if tx['kind']=='WRITE' else 1,
        ram_addr=0 if tx is None else tx['address'],ram_data=0 if tx is None else tx['value'],
        cycles=event['cycles'],cumulative_cycles=event['cumulative_cycles'],
        event=0 if event['retired'] else 1 if event['event']=='TRAP' else 2,
        halted=int(machine.status=='HALTED'),trapped=int(machine.status=='TRAP'))


def make_case(directory, name, words, *, ram=None, entry=0, initial=None,
              keys=0, key_schedule=None, stop=None, limit=100000,
              memory_mode=0, rom_delay_ps=0, ram_delay_ps=0, kind='instruction'):
    if len(words)>4096:raise ValueError('ROM overflow')
    loaded_words=len(words)
    image=tuple(words)+(0xFFFF,)*(4096-len(words))
    ram=[10]*256 if ram is None else list(ram)
    values=INITIAL | (initial or {})
    cpu=Machine(image,ram=ram,pc=entry,keys=keys,trace=False)
    for field,value in values.items():setattr(cpu,field,value)
    expected=[];inputs=[]
    for i in range(limit):
        if stop is not None and i and stop(cpu,i):break
        current=keys if key_schedule is None else key_schedule(cpu,i)
        cpu.keys=current;inputs.append(current)
        event=cpu.step()
        if event is None:raise AssertionError(f'{name}: attempted event after terminal state')
        expected.append(observed(event,i,cpu))
        if cpu.status!='RUNNING':break
    else:
        raise AssertionError(f'{name}: expected generation exceeded {limit} instructions')
    if not expected:raise AssertionError(f'{name}: empty scenario')
    directory.mkdir(parents=True,exist_ok=True)
    (directory/f'{name}.rom.memh').write_text(''.join(f'{w:04X}\n' for w in image))
    (directory/f'{name}.ram.memh').write_text(''.join(f'{v:X}\n' for v in ram))
    (directory/f'{name}.keys.txt').write_text(''.join(f'{k}\n' for k in inputs))
    (directory/f'{name}.expected.jsonl').write_text(''.join(json.dumps(row,separators=(',',':'))+'\n' for row in expected))
    (directory/f'{name}.expected_ram.memh').write_text(''.join(f'{v:X}\n' for v in cpu.ram))
    row=dict(name=name,rom_words=loaded_words,entry=entry,initial=values,keys=keys,
             events=len(expected),cycles=cpu.cycles,retired=cpu.retired,
             ram_reads=cpu.ram_reads,ram_writes=cpu.ram_writes,
             memory_mode=memory_mode,rom_delay_ps=rom_delay_ps,ram_delay_ps=ram_delay_ps,
             kind=kind,status=cpu.status,
             binary_sha256=hashlib.sha256(b''.join(w.to_bytes(2,'little') for w in words)).hexdigest())
    fields=[name,loaded_words,entry,values['a'],values['ar'],values['z'],values['c'],values['gpo'],
            keys,len(expected),cpu.cycles+40,memory_mode,rom_delay_ps,ram_delay_ps]
    return row,' '.join(map(str,fields))


def instruction_specs():
    # Independent integer arithmetic is also exhausted in the standalone RTL ALU
    # bench; this CPU sequence checks decoder, enables and old-carry propagation.
    words=[]
    for carry in range(2):
        for a in range(16):
            for major in range(7):
                for immediate in range(16):
                    words += [0,0x3000 if carry else 0x1000,a,(major<<12)|immediate]
    words.append(0xF100)
    # Split into ROM-sized images, without changing the exercised operations.
    for index,start in enumerate(range(0,len(words)-1,3072)):
        yield dict(name=f'immediates_{index}',words=words[start:min(start+3072,len(words)-1)]+[0xF100])
    for indirect in (False,True):
        words=[0xA10A,0xA005]
        for carry in range(2):
            for a in (0,7,15):
                for rhs in (0,1,15):
                    for sub in range(10):
                        words += [rhs,0x81A5,0,0x3000 if carry else 0x1000,a,
                                  (0x9000 if indirect else 0x8000)|sub<<8|(0 if indirect else 0xA5)]
        yield dict(name=f'ram_alu_{int(indirect)}',words=words+[0xF100])
    words=[]
    for address in range(256):
        words += [0xA100|(address>>4),0xA000|(address&15),address&15,
                  0x8100|address,0x9000,0x1001,0x9100,0x8000|address]
    yield dict(name='all_ram_addresses',words=words+[0xF100])
    for z in range(2):
        for c in range(2):
            words=[]
            for k in range(64):
                words += [0xE000,0xE200,0xE100,0xE200,0xA400,0xA500,0xA600]
            yield dict(name=f'io_ar_flags_{z}_{c}',words=words+[0xF100],
                initial=dict(z=z,c=c,ar=255),
                key_schedule=lambda cpu,i:min(i//7,63))
    words=[0x8110,0xF100]+[0xFFFF]*4093+[0x0009]
    yield dict(name='pc_fff_wrap',words=words,entry=4095)
    branching=assemble('''LDI 0
ADDI 0
JZ zero
.word 0xFFFF
zero: JC bad
LDI 15
ADDI 1
JC carry
.word 0xFFFF
carry: JZ wrapzero
.word 0xFFFF
wrapzero: LDI 2
SUBI 1
JZ bad
JC noborrow
bad: .word 0xFFFF
noborrow: SUBI 2
JC bad
JZ bad
JMP done
.word 0xFFFF
done: HALT''').words
    yield dict(name='branches_taken_and_not_taken',words=branching)
    for word in (0x0010,0x0100,0x10F0,0x7300,0x7001,0x8A00,0x9001,0x9F00,
                 0xA010,0xA201,0xA700,0xE001,0xE300,0xF001,0xF200,0xFFFF):
        yield dict(name=f'trap_{word:04x}',words=[word],initial=dict(a=9,ar=0x45,z=0,c=1,gpo=6))
    # Physical full ROM model sees FFFF, while Python's original short-image
    # FAULT remains a separate software/metadata diagnostic, not CPU hardware.
    yield dict(name='unloaded_is_physical_trap',words=[])
    rng=random.Random(0x203001)
    names=['LDI','ADDI','ADCI','SUBI','SBCI','ANDI','XORI','SHL','SHR','NOT',
           'LD','ST','ADD','ADC','SUB','SBC','CMP','AND','XOR','OR',
           'ARL','ARH','MOVARL','MOVARH','MOVA_ARL','MOVA_ARH','INCAR','IN0','IN1','OUT','NOP']
    for n in range(16):
        words=[]
        for i in range(128):
            if rng.randrange(10)==0:
                words.append(encode(rng.choice(['JMP','JZ','JC']),min(128,i+rng.randrange(1,7))))
                continue
            name=rng.choice(names)
            if name in ('LDI','ADDI','ADCI','SUBI','SBCI','ANDI','XORI','ARL','ARH'):
                word=encode(name,rng.randrange(16))
            elif name in ('LD','ST','ADD','ADC','SUB','SBC','CMP','AND','XOR','OR'):
                indirect=bool(rng.randrange(2))
                word=encode(name,None if indirect else rng.randrange(256),indirect=indirect)
            else:word=encode(name)
            words.append(word)
        yield dict(name=f'random_program_{n:02d}',words=words+[0xF100],
                   keys=n*3,initial=dict(a=n&15,ar=(n*17)&255,z=n&1,c=(n>>1)&1))
    mixed=assemble('''ARH 2
ARL 3
LDI 15
ST [AR]
ADDI 1
ADC [AR]
ST 0x24
LD 0x24
CMP [AR]
LDI 0
SBC [AR]
OUT
HALT''').words
    yield dict(name='delayed_async_bus',words=mixed,rom_delay_ps=1500,ram_delay_ps=2000)
    yield dict(name='sync_ram_adapter',words=mixed,memory_mode=1,rom_delay_ps=1500)


def game_specs():
    for name,program in programs().items():
        stop_boot=program.symbols['tick'] if name=='pong' else program.symbols['tick_done']
        yield dict(name=f'{name}_boot',words=program.words,stop=lambda cpu,i,p=stop_boot:cpu.pc==p,
                   kind='game_boot')
        cases=pong_cases(0) if name=='pong' else snake_cases(0)
        for label,ram,keys in cases:
            if label.startswith('all_keys_'):continue
            boundary=program.symbols['tick_done']
            yield dict(name=f'{name}_{label}',words=program.words,ram=ram,keys=keys,
                entry=program.symbols['tick'],stop=lambda cpu,i,p=boundary:cpu.pc==p,kind='game_tick')
        # Real CPU continuation: initialize once, then provide only key events.
        state=dict(visits=0,ticks=0,key=0)
        boundary=program.symbols['tick_done'];tick=program.symbols['tick']
        target=64+(1 if name=='snake' else 0)
        def stop_replay(cpu,i,s=state,p=boundary,target=target):
            if cpu.pc==p:s['visits']+=1
            return s['visits']>=target
        def keys_replay(cpu,i,s=state,p=tick,game=name):
            if cpu.pc==p:
                k=s['ticks'];s['ticks']+=1
                rectangle=[4]*13+[1]*5+[8]*13+[2]*5
                s['key']=(k//8)%16 if game=='pong' else (8 if k<10 else 2 if k<13 else rectangle[(k-13)%36])
            return s['key']
        yield dict(name=f'{name}_continuous_64',words=program.words,stop=stop_replay,
                   key_schedule=keys_replay,kind='game_continuous_64')
        for mode in (0,1):
            ram=next(c[1] for c in (pong_cases(0) if name=='pong' else snake_cases(0)) if c[0]=='normal')
            yield dict(name=f'{name}_memory_mode_{mode}',words=program.words,ram=ram,
                entry=tick,stop=lambda cpu,i,p=boundary:cpu.pc==p,memory_mode=mode,
                rom_delay_ps=1500,ram_delay_ps=2000 if mode==0 else 0,kind='game_memory_stress')


def prepare(output):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    (output/'inputs_manifest.json').write_text(json.dumps(source_fingerprints(),indent=2)+'\n')
    for suite,specifications in [('instructions',instruction_specs()),('games',game_specs())]:
        directory=output/suite;rows=[];lines=[]
        for spec in specifications:
            spec=dict(spec);name=spec.pop('name');words=spec.pop('words')
            row,line=make_case(directory,name,words,**spec);rows.append(row);lines.append(line)
        (directory/'cases.txt').write_text('\n'.join(lines)+'\n')
        metadata=dict(isa_id=ISA_VERSION,timing_profile=TIMING_PROFILE,suite=suite,
                      status='EXPECTED_ONLY_NOT_RTL_PASS',cases=rows)
        (directory/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
        print(f'PREPARED {suite}: {len(rows)} cases, {sum(r["events"] for r in rows)} expected events')
    return 0


def summarize(output):
    """Bind actual runs to the sources present before compile, not a Git hash."""
    output=Path(output).resolve()
    fingerprints=json.loads((output/'inputs_manifest.json').read_text())
    if fingerprints!=source_fingerprints():raise DifferentialError('sources changed during simulation; rerun required')
    rules=json.loads((ROOT/'docs/m20/isa_v0_1.json').read_text())['encoding_rules']
    coverage=Counter();changes=Counter();totals={};rom_images={}
    for suite in ('instructions','games'):
        comparison=json.loads((output/suite/'comparison.json').read_text())
        if comparison['status']!='PASS':raise DifferentialError(f'{suite}: comparison incomplete')
        totals[suite]={k:comparison[k] for k in ('case_count','events','cycles')}
        metadata=json.loads((output/suite/'metadata.json').read_text())
        for case in metadata['cases']:
            if case['kind']=='game_boot':rom_images[case['name']]=case['binary_sha256']
            previous=case['initial']
            with (output/suite/f'{case["name"]}.rtl.csv').open() as f:
                for raw in csv.DictReader(f):
                    row={k:int(v) for k,v in raw.items()}
                    if row['event']==0:
                        matches=[r for r in rules if row['word']&int(r['mask'],16)==int(r['value'],16)]
                        if len(matches)!=1:raise DifferentialError('actual retired instruction has invalid encoding')
                        coverage[matches[0]['id']]+=1
                        pattern=','.join(f'{k}_changed={int(previous[k]!=row[k])}' for k in ('a','z','c'))
                        changes[pattern]+=1
                    previous=row
    if set(coverage)!=set(r['id'] for r in rules):raise DifferentialError('not all 45 encoding rules executed')
    isa_log=(output/'xsim/isa.log').read_text()
    if 'M20_ISA_PASS words=65536 legal=15015 illegal=50521 alu_vectors=32768' not in isa_log:
        raise DifferentialError('missing exhaustive RTL unit result')
    if 'M20_MEMORY_PASS checks=7 ' not in (output/'xsim/memory.log').read_text():
        raise DifferentialError('missing memory/reset RTL result')
    python_log=(output/'python_tests.log').read_text()
    count=re.search(r'Ran (\d+) tests',python_log)
    if not count or not python_log.rstrip().endswith('OK'):raise DifferentialError('Python regression not complete')
    for suite in ('instructions','games'):
        if f'M20_CPU_PASS cases={totals[suite]["case_count"]}' not in (output/f'xsim/{suite}.log').read_text():
            raise DifferentialError(f'missing actual RTL completion for {suite}')
    protection='NO_PRIOR_BASELINE_AVAILABLE'
    baseline=output/'baseline.json'
    if baseline.exists():
        original=json.loads(baseline.read_text())
        for path,digest in (original['legacy_files']|original['sources']).items():
            if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:
                raise DifferentialError(f'protected original file changed: {path}')
        if hashlib.sha256((ROOT/'.git/index').read_bytes()).hexdigest()!=original['git_index_sha256']:
            raise DifferentialError('Git index changed')
        protection='PASS_308_LEGACY_FILES_AND_REFERENCE_INPUTS_AND_GIT_INDEX'
    result=dict(status='PASS',isa_id=ISA_VERSION,timing_profile=TIMING_PROFILE,
        tool=(output/'tool_version.log').read_text().strip(),python_tests=int(count.group(1)),
        core_state_bits=33,rtl_encoding_words=65536,rtl_legal_words=15015,rtl_illegal_words=50521,
        rtl_alu_vectors=32768,memory_checks=7,executed_encoding_rules=dict(coverage),
        observed_register_flag_change_patterns=dict(changes),suites=totals,game_rom_sha256=rom_images,
        protected_original_files=protection,source_fingerprints=fingerprints,
        limits='Behavioral RTL simulation only; no synthesis, STA, physical timing or 157 gate-count proof')
    (output/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    (output/'coverage.json').write_text(json.dumps(dict(encoding_rule_count=len(rules),
        executed_encoding_rules=dict(coverage),observed_register_flag_change_patterns=dict(changes)),indent=2)+'\n')
    print(f'M20_EVIDENCE_PASS sources={len(fingerprints)} rules={len(coverage)} python_tests={count.group(1)}')
    return 0


class DifferentialError(AssertionError):pass


def compare(directory):
    directory=Path(directory).resolve()
    metadata=json.loads((directory/'metadata.json').read_text())
    results=[]
    for case in metadata['cases']:
        name=case['name']
        expected=[json.loads(line) for line in (directory/f'{name}.expected.jsonl').read_text().splitlines()]
        path=directory/f'{name}.rtl.csv'
        try:
            with path.open() as f:
                reader=csv.DictReader(f)
                if tuple(reader.fieldnames or ())!=FIELDS:raise DifferentialError(f'{name}: bad CSV header {reader.fieldnames}')
                actual=[{k:int(v) for k,v in row.items()} for row in reader]
        except (ValueError,TypeError) as exc:
            raise DifferentialError(f'{name}: nonnumeric/X/Z or malformed RTL output: {exc}') from exc
        if len(actual)!=len(expected):raise DifferentialError(f'{name}: events expected {len(expected)}, actual {len(actual)}')
        for i,(gold,got) in enumerate(zip(expected,actual)):
            fields=list(FIELDS)
            if gold['ram_kind']==0:fields.remove('ram_addr');fields.remove('ram_data')
            if any(gold[k]!=got[k] for k in fields):
                failure=dict(test=name,instruction_index=i,pc=gold['pc'],instruction_word=gold['word'],
                             expected=gold,actual=got,inputs=str(directory/f'{name}.rom.memh'))
                (directory/'first_mismatch.json').write_text(json.dumps(failure,indent=2)+'\n')
                raise DifferentialError(json.dumps(failure,indent=2))
        gold_ram=[int(w,16) for w in (directory/f'{name}.expected_ram.memh').read_text().split()]
        try:got_ram=[int(w,16) for w in (directory/f'{name}.ram.final.memh').read_text().split()]
        except ValueError as exc:raise DifferentialError(f'{name}: unknown/malformed final RAM') from exc
        if gold_ram!=got_ram:
            mismatch=[(i,gold_ram[i],got_ram[i] if i<len(got_ram) else None) for i in range(256)
                      if i>=len(got_ram) or gold_ram[i]!=got_ram[i]]
            raise DifferentialError(f'{name}: final RAM mismatch, length {len(got_ram)}, first {mismatch[:8]}')
        results.append(dict(name=name,events=len(actual),cycles=case['cycles'],retired=case['retired'],
                            ram_reads=case['ram_reads'],ram_writes=case['ram_writes'],kind=case['kind'],status='PASS'))
    result=dict(status='PASS',isa_id=metadata['isa_id'],timing_profile=metadata['timing_profile'],
                suite=metadata['suite'],case_count=len(results),events=sum(r['events'] for r in results),
                cycles=sum(r['cycles'] for r in results),cases=results,
                evidence='Actual XSIM CSV and complete final RAM matched independent Python interpreter')
    (directory/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'RTL_DIFF_PASS {result["suite"]}: {len(results)} cases, {result["events"]} events')
    return 0


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    p=commands.add_parser('prepare');p.add_argument('--output',required=True,type=Path)
    p=commands.add_parser('compare');p.add_argument('--directory',required=True,type=Path)
    p=commands.add_parser('summarize');p.add_argument('--output',required=True,type=Path)
    args=parser.parse_args(argv)
    try:
        if args.command=='prepare':return prepare(args.output)
        if args.command=='summarize':return summarize(args.output)
        return compare(args.directory)
    except (OSError,ValueError,AssertionError) as exc:
        parser.exit(1,f'M20_RTL_REGRESSION_FAIL: {exc}\n')


if __name__=='__main__':raise SystemExit(main())
