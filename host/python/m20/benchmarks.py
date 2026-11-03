"""Reproducible machine-program validation and measured instruction budgets.

Game reference functions only check results; they never drive Machine execution
or write its RAM after the initial test fixture / CPU reset boundary.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import random

from .assembler import assemble
from .machine import Machine
from .game_reference import (PONG_FIELDS, SNAKE_FIELDS, get8, pong_initial,
    pong_tick, snake_fixture, snake_initial, snake_tick, snake_invariants)
from .isa import ISA_VERSION

ROOT = Path(__file__).resolve().parents[3]
SEED = 0x2030028


def programs():
    return {name: assemble((ROOT/'software/m20_300'/f'{name}.asm').read_text(),
                           filename=f'software/m20_300/{name}.asm')
            for name in ('pong', 'snake')}


def drive(cpu, stop_pc, limit=100000, allowed_writes=None):
    histogram = Counter()
    for _ in range(limit):
        if cpu.pc == stop_pc:
            return histogram
        if cpu.status != 'RUNNING':
            raise AssertionError(f'CPU {cpu.status}: {cpu.reason}, PC={cpu.pc:03X}')
        event = cpu.step()
        if not event['retired']:
            raise AssertionError(f'non-retire CPU event: {event}')
        tx=event['ram_transaction']
        if allowed_writes is not None and tx and tx['kind']=='WRITE':
            assert tx['address'] in allowed_writes, f'unexpected write {tx}'
        histogram[event['mnemonic']] += 1
    if cpu.pc == stop_pc:
        return histogram
    raise AssertionError('instruction bound exceeded')


def compare_ram(name, actual, expected, case):
    fields = PONG_FIELDS if name == 'pong' else SNAKE_FIELDS
    mismatch = [(a, expected[a], actual[a]) for a in fields if actual[a] != expected[a]]
    if mismatch:
        raise AssertionError(f'{name}/{case}: RAM address,expected,actual {mismatch[:12]}')
    if name == 'snake' and actual[11] != 3:
        snake_invariants(actual)


def pong_cases(random_cases=1000):
    initial = pong_initial()
    directed = [
        ('normal', {}, 0), ('upper_wall', {1:0,3:1}, 0),
        ('lower_wall', {1:7,3:0}, 0),
        ('left_paddle', {0:1,1:2,2:1,3:0}, 0),
        ('right_paddle', {0:14,1:2,2:0,3:0}, 0),
        ('wall_and_paddle', {0:1,1:0,2:1,3:1,4:0}, 0),
        ('right_score', {0:1,1:5,2:1,3:0,4:0}, 0),
        ('left_score', {0:14,1:5,2:0,3:0,5:0}, 0),
        ('left_score_carry', {0:14,1:5,2:0,5:0,6:15,7:7}, 0),
        ('right_score_wrap', {0:1,1:5,2:1,4:0,8:15,9:15}, 0),
        ('upper_paddle_clamp', {4:0,5:0}, 5),
        ('lower_paddle_clamp', {4:5,5:5}, 10),
        ('score_wall_two_paddles', {0:14,1:7,2:0,3:0,4:0,5:0,6:15,7:7}, 10),
    ]
    for label, changes, keys in directed:
        ram = initial.copy()
        for a,v in changes.items():ram[a] = v
        yield label, ram, keys
    for keys in range(64):
        yield f'all_keys_{keys:02d}', initial.copy(), keys
    rng = random.Random(SEED)
    for i in range(random_cases):
        ram = initial.copy()
        ram[:6] = [rng.randrange(1,15),rng.randrange(8),rng.randrange(2),
                   rng.randrange(2),rng.randrange(6),rng.randrange(6)]
        ram[6:10] = [rng.randrange(16) for _ in range(4)]
        yield f'random_{i:05d}', ram, rng.randrange(64)


def serpentine():
    return [(x,y) for y in range(8) for x in
            (range(16) if y%2 == 0 else range(15,-1,-1))]


def snake_cases(random_cases=1000):
    init_points = [(2,3),(3,3),(4,3)]
    yield 'normal', snake_initial(), 0
    yield 'grow', snake_fixture(init_points,food=(5,3)), 0
    yield 'score_wrap', snake_fixture(init_points,food=(5,3),score=255), 0
    yield 'ring_index_wrap', snake_fixture(init_points,tail_index=61), 0
    yield 'right_wall', snake_fixture([(13,3),(14,3),(15,3)]), 0
    yield 'left_wall', snake_fixture([(2,3),(1,3),(0,3)],direction=2), 0
    yield 'upper_wall', snake_fixture([(5,2),(5,1),(5,0)],direction=3), 0
    yield 'lower_wall', snake_fixture([(5,5),(5,6),(5,7)],direction=1), 0
    square = [(3,3),(3,4),(4,4),(4,3)]
    yield 'legal_old_tail', snake_fixture(square,direction=3), 4
    yield 'self_collision', snake_fixture([(1,1),(2,1),(3,1),(3,2),(2,2)],direction=2), 1
    yield 'opposite_direction_ignored', snake_initial(), 4
    yield 'key_priority', snake_initial(), 15
    yield 'dead_no_start', snake_fixture(init_points,status=1), 1
    yield 'win_no_start', snake_fixture(init_points,status=2), 8
    yield 'restart', snake_fixture(init_points,status=1,score=173), 32
    path = serpentine()
    yield 'grow_to_64', snake_fixture(list(reversed(path[1:64])),direction=2,
                                      food=(0,0),score=255,tail_index=3), 0
    yield 'food_search_63', snake_fixture(list(reversed(path[2:64])),direction=2,
                                         food=(1,0),score=255), 0
    for keys in range(64):
        yield f'all_keys_{keys:02d}', snake_initial(), keys
    rng = random.Random(SEED + 1)
    for i in range(random_cases):
        length = rng.randrange(3,64)
        if i%2 == 0:
            start = rng.randrange(129-length)
            points = path[start:start+length]
        else:
            # Cover arbitrary turns as well as long, dense serpentine bodies.
            points=[(rng.randrange(16),rng.randrange(8))]
            while len(points)<length:
                x,y=points[-1]
                choices=[p for p in ((x+1,y),(x,y+1),(x-1,y),(x,y-1))
                         if 0<=p[0]<16 and 0<=p[1]<8 and p not in points]
                if not choices:break
                points.append(rng.choice(choices))
            if len(points)<3:points=[(2,3),(3,3),(4,3)]
        if rng.randrange(2):points = list(reversed(points))
        delta = (points[-1][0]-points[-2][0], points[-1][1]-points[-2][1])
        direction = {(1,0):0,(0,1):1,(-1,0):2,(0,-1):3}[delta]
        free = [q for q in path if q not in points]
        ram = snake_fixture(points,direction=direction,food=rng.choice(free),
                            tail_index=rng.randrange(64),score=rng.randrange(256))
        yield f'random_{i:05d}', ram, rng.randrange(32)


def run_case(name, program, label, ram, keys, trace=False):
    expected = (pong_tick if name == 'pong' else snake_tick)(ram,keys)
    cpu = Machine(program.words,ram=ram,pc=program.symbols['tick'],keys=keys,trace=trace)
    allowed=(set(range(13))|{0x20,0xF0}) if name=='pong' else (
        set(range(256)) if keys&32 else set(range(0x22))|set(range(0x40,0xE0))|{0xF0})
    histogram = drive(cpu,program.symbols['tick_done'],allowed_writes=allowed)
    compare_ram(name,cpu.ram,expected,label)
    assert cpu.rom_reads == cpu.retired
    assert cpu.cycles == 2*cpu.retired + 3*(cpu.ram_reads+cpu.ram_writes)
    assert cpu.gpio_writes == 0, 'core-only programs must not pretend to refresh OLED'
    row = dict(program=name,case=label,kind='valid_core_tick',keys=keys,
       retired=cpu.retired,rom_reads=cpu.rom_reads,ram_reads=cpu.ram_reads,
       ram_writes=cpu.ram_writes,gpio_writes=cpu.gpio_writes,cycles=cpu.cycles,
       reset_cycles=cpu.reset_cycles,total_cycles=cpu.total_cycles,
       loop_turnaround_cycles=4,cycles_with_loop=cpu.cycles+4,
       status='PASS',head_probes=get8(cpu.ram,15) if name=='snake' else 0)
    return row,cpu,histogram


def boot_case(name, program):
    cpu=Machine(program.words,ram=[10]*256,trace=False)
    drive(cpu,program.symbols['tick'] if name=='pong' else program.symbols['tick_done'])
    compare_ram(name,cpu.ram,pong_initial() if name=='pong' else snake_initial(),'dirty_RAM_boot')
    assert cpu.cycles == 2*cpu.retired + 3*(cpu.ram_reads+cpu.ram_writes)
    return cpu.summary()


def replay(name, program, ticks=512):
    cpu=Machine(program.words,ram=[10]*256,trace=False)
    boundary=program.symbols['tick_done']
    drive(cpu,program.symbols['tick'] if name=='pong' else boundary)
    expected=pong_initial() if name=='pong' else snake_initial()
    checks=0
    rectangle=[4]*13+[1]*5+[8]*13+[2]*5
    start_retired,start_cycles=cpu.retired,cpu.cycles
    for i in range(ticks):
        keys=(i//8)%16 if name=='pong' else (8 if i<10 else 2 if i<13 else rectangle[(i-13)%36])
        cpu.keys=keys
        if cpu.pc==boundary:
            assert cpu.step()['mnemonic']=='NOP'
            assert cpu.step()['mnemonic']=='JMP'
        expected=(pong_tick if name=='pong' else snake_tick)(expected,keys)
        drive(cpu,boundary)
        compare_ram(name,cpu.ram,expected,f'replay_{i}')
        if name=='snake':assert cpu.ram[11]==0, 'scripted replay must stay alive'
        checks+=1
    return dict(ticks=checks,retired=cpu.retired-start_retired,
                cycles=cpu.cycles-start_cycles,live_cpu_continuation=True,
                host_RAM_writes_after_boot=0,inputs='fixed external key event sequence')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--random-cases',type=int,default=1000)
    args=parser.parse_args(argv)
    if not 0<=args.random_cases<=10000:parser.error('random cases 0..10000')
    output=args.output;output.mkdir(parents=True,exist_ok=True)
    compiled=programs();metrics=[];summary={};coverage={}
    with (output/'fixtures.jsonl').open('w') as fixtures:
        for name,program in compiled.items():
            dest=output/name;dest.mkdir(exist_ok=True)
            (dest/f'{name}.bin').write_bytes(program.binary)
            (dest/f'{name}.memh').write_text(program.memh)
            (dest/'symbols.json').write_text(json.dumps(program.symbols,indent=2)+'\n')
            (dest/'listing.json').write_text(json.dumps(program.listing,indent=2)+'\n')
            lines=[f"{r['address']:03X}: {r['word']:04X}  {r.get('source','')}" for r in program.listing]
            (dest/f'{name}.lst').write_text('\n'.join(lines)+'\n')
            group=[];hist=Counter();max_input=None;maximum=-1
            cases=pong_cases(args.random_cases) if name=='pong' else snake_cases(args.random_cases)
            for label,ram,keys in cases:
                row,cpu,counts=run_case(name,program,label,ram,keys)
                metrics.append(row);group.append(row);hist.update(counts)
                fixtures.write(json.dumps(dict(program=name,case=label,keys=keys,ram=ram),separators=(',',':'))+'\n')
                if row['cycles']>maximum:
                    maximum=row['cycles'];max_input=(label,ram,keys)
            label,ram,keys=max_input
            row,cpu,_=run_case(name,program,label,ram,keys,trace=True)
            with (dest/'max_case_trace.jsonl').open('w') as trace:
                for event in cpu.trace:trace.write(json.dumps(event,separators=(',',':'))+'\n')
            (dest/'max_case_input.json').write_text(json.dumps(dict(case=label,keys=keys,ram=ram),indent=2)+'\n')
            cases_by_name={r['case']:r for r in group}
            summary[name]=dict(rom_words=len(program.words),emitted_words=program.used_words,
                rom_bytes=len(program.binary),rom_capacity_words=4096,
                rom_utilization=len(program.words)/4096,
                binary_sha256=hashlib.sha256(program.binary).hexdigest(),
                source_sha256=hashlib.sha256((ROOT/'software/m20_300'/f'{name}.asm').read_bytes()).hexdigest(),
                cases=len(group),minimum_cycles=min(r['cycles'] for r in group),
                maximum_cycles=maximum,maximum_case=label,maximum_case_metrics=row,
                selected_cases={k:v for k,v in cases_by_name.items() if not k.startswith(('random_','all_keys_'))},
                boot=boot_case(name,program),replay=replay(name,program),
                interpretation='Measured maxima over saved fixtures, not exhaustive timing or physical CPU Fmax.')
            coverage[name]=dict(hist)
    with (output/'case_metrics.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(metrics[0]));writer.writeheader();writer.writerows(metrics)
    summary=dict(status='PASS',isa_version=ISA_VERSION,random_seed=SEED,
        format_version=1,
        random_cases_per_game=args.random_cases,programs=summary,
        timing_model='ordinary 2 / RAM 5 microcycles; reset 1 separate; no RTL/physical timing proof',
        scope='CPU core algorithms only; no OLED/SPI or key-debounce program',
        host_algorithms='Independent validation oracle only; no Machine game shortcuts',
        software_instruction_histograms=coverage)
    source_paths=(sorted((ROOT/'host/python/m20').glob('*.py'))+
                  sorted((ROOT/'host/python/tests').glob('test_m20*.py'))+
                  sorted((ROOT/'software/m20_300').glob('*.asm'))+
                  [ROOT/'docs/m20/M20_300_architecture_v0_1.md'])
    summary['source_fingerprints']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in source_paths}
    # These are assumed microclock rates, never measured FPGA/157 frequencies.
    budget=[]
    for name,program in summary['programs'].items():
        for case,row in program['selected_cases'].items():
            for hz in (100000,1000000,2000000,5000000):
                budget.append(dict(program=name,case=case,microclock_hz=hz,
                    execution_cycles=row['cycles'],continuous_loop_cycles=row['cycles_with_loop'],
                    execution_seconds=row['cycles']/hz,
                    continuous_loop_seconds=row['cycles_with_loop']/hz,
                    clock_source='ASSUMED_NOT_MEASURED',scope='CORE_ONLY_NO_OLED_OR_WAIT'))
    with (output/'clock_budget.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(budget[0]));writer.writeheader();writer.writerows(budget)
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:{n:v[n] for n in ['rom_words','rom_bytes','cases','maximum_cycles','maximum_case']} for k,v in summary['programs'].items()},indent=2))
    return 0


if __name__=='__main__':raise SystemExit(main())
