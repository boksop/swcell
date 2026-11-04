#!/usr/bin/env python3
"""Independent rule checks and real-RTL fixtures for the new software variant."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'host/python'))
from m20 import Machine,assemble
from m20.benchmarks import snake_cases
from m20.game_reference import snake_tick,snake_fixture,snake_invariants,is_occupied,set_occupied,get8,put8,SNAKE_FIELDS
from m20.rtl_regression import make_case

VARIANT=ROOT/'software/m20_300/variants/snake_shuffled_v0_1'

def drive(m,boundary):
    for _ in range(30000):
        if m.pc==boundary:return
        assert m.step() is not None and m.status=='RUNNING'
    raise ValueError('variant exceeded instruction bound')

def oracle(before,keys,table):
    expected=snake_tick(before,keys)
    if expected[14]==1 and expected[11]==0:
        index=get8(before,34)
        for count in range(1,66):
            index=(index+1)%128;x,y=table[index]
            if not is_occupied(expected,(x,y)):
                expected[7:9]=[x,y];put8(expected,15,count);put8(expected,34,index);break
        else:raise AssertionError('valid body has no food slot')
    return expected

def grow_fixture(point):
    x,y=point
    for direction,(dx,dy) in enumerate(((1,0),(0,1),(-1,0),(0,-1))):
        body=[(x-3*dx,y-3*dy),(x-2*dx,y-2*dy),(x-dx,y-dy)]
        if all(0<=a<16 and 0<=b<8 for a,b in body):return snake_fixture(body,direction=direction,food=point)
    raise ValueError('cannot construct growth fixture')

def prepare(out):
    if out.exists():raise ValueError('fresh output required')
    out.mkdir(parents=True)
    program=assemble((VARIANT/'snake_shuffled.asm').read_text())
    table=[tuple(p) for p in json.loads((VARIANT/'food_table.json').read_text())['positions']]
    rows=[];lines=[];probes=[]
    def add(name,ram,keys,entry=None):
        entry=program.symbols['tick'] if entry is None else entry
        row,line=make_case(out,name,program.words,ram=ram,entry=entry,keys=keys,
            stop=lambda cpu,i:cpu.pc==program.symbols['tick_done'],limit=30000,kind='snake_shuffled')
        rows.append(row);lines.append(line)
    # Every possible table index, including127->0, is tested by real growth.
    for index,point in enumerate(table):
        ram=grow_fixture(point);put8(ram,34,index)
        expected=oracle(ram,0,table)
        machine=Machine(program.words,ram=ram,pc=program.symbols['tick'],trace=False)
        drive(machine,program.symbols['tick_done'])
        assert all(machine.ram[a]==expected[a] for a in (*SNAKE_FIELDS,34,35)),index
        snake_invariants(machine.ram);probes.append(get8(machine.ram,15))
        add(f'grow_index_{index:03d}',ram,0)
    # Original directed cases plus deterministic legal random bodies and all keys.
    for name,ram,keys in snake_cases(100):
        put8(ram,34,table.index((ram[7],ram[8])))
        expected=oracle(ram,keys,table)
        machine=Machine(program.words,ram=ram,pc=program.symbols['tick'],keys=keys,trace=False)
        drive(machine,program.symbols['tick_done'])
        assert all(machine.ram[a]==expected[a] for a in (*SNAKE_FIELDS,34,35)),name
        if machine.ram[11]!=3:snake_invariants(machine.ram)
        add(name,ram,keys)
    # Food routine unit inputs: arbitrary occupancy bitmaps, independent of a body.
    for blocked in (1,7,63,64,65):
        ram=[0]*256;put8(ram,34,127)
        for index in range(blocked):set_occupied(ram,table[index],True)
        machine=Machine(program.words,ram=ram,pc=program.symbols['food_next_candidate'],trace=False)
        drive(machine,program.symbols['tick_done'])
        if blocked<65:
            assert machine.ram[7:9]==list(table[blocked]) and get8(machine.ram,15)==blocked+1
        else:assert machine.ram[11]==3 and machine.ram[14]==5 and get8(machine.ram,15)==65
        add(f'bitmap_prefix_{blocked}',ram,0,program.symbols['food_next_candidate'])
    # Dirty RAM boot proves the two new index cells are CPU-initialized.
    add('dirty_boot',[10]*256,0,0)
    (out/'cases.txt').write_text('\n'.join(lines)+'\n')
    (out/'metadata.json').write_text(json.dumps(dict(isa_id='M20-300-ISA-0.1',timing_profile='M20-300-V1-TIMING-0.1',suite='snake_shuffled',cases=rows),indent=2)+'\n')
    result=dict(status='EXPECTED_PREPARED_NOT_RTL_PASS',cases=len(rows),events=sum(r['events'] for r in rows),
                growth_index_cases=128,table_unique_positions=len(set(table)),max_probe_in_growth=max(probes),
                bitmap_unit_note='prefix occupancy is a standalone routine test;65blocked is deliberate invalid/fullness negative',
                frozen_original_modified=False)
    (out/'preparation.json').write_text(json.dumps(result,indent=2)+'\n');print('SNAKE_SHUFFLED_RULES_PASS',json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);prepare(p.parse_args().output)
