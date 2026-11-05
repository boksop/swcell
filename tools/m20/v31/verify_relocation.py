#!/usr/bin/env python3
"""Original software versus relocated tick routines, independent game oracle."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'host/python'));sys.path.insert(0,str(Path(__file__).parent))
from build_firmware import firmware,VARS
from m20 import Machine,assemble
from m20.benchmarks import pong_cases,snake_cases
from m20.game_reference import PONG_FIELDS,SNAKE_FIELDS,pong_tick,put8,set_occupied


def run(out):
    spec=importlib.util.spec_from_file_location('shuffled_oracle',ROOT/'tools/m20/v3_snake_shuffled_verify.py')
    oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
    _,image,_=firmware();table=[tuple(p) for p in json.loads((oracle.VARIANT/'food_table.json').read_text())['positions']]
    counts={'pong':0,'snake':0}
    def check(prefix,ram,keys,entry,expected=None):
        new=Machine(image.words,ram=ram,pc=image.symbols[prefix+'_'+entry],trace=False)
        new.ram[VARS['PLAYKEYS']]=keys&15;new.ram[VARS['STABLE1']]=(keys>>4)&3
        new.run(30000,stop_pc=image.symbols[prefix+'_tick_done'])
        assert new.pc==image.symbols[prefix+'_tick_done'] and new.status=='RUNNING'
        original=ROOT/('software/m20_300/pong.asm' if prefix=='P' else 'software/m20_300/variants/snake_shuffled_v0_1/snake_shuffled.asm')
        base=assemble(original.read_text());ref=Machine(base.words,ram=ram,keys=keys,pc=base.symbols[entry],trace=False)
        ref.run(30000,stop_pc=base.symbols['tick_done']);assert ref.pc==base.symbols['tick_done']
        fields=PONG_FIELDS if prefix=='P' else (*SNAKE_FIELDS,34,35)
        assert all(new.ram[a]==ref.ram[a] for a in fields),(prefix,entry,keys)
        if expected is not None:assert all(new.ram[a]==expected[a] for a in fields)
        counts['pong' if prefix=='P' else 'snake']+=1
    for _,ram,keys in pong_cases(100):check('P',ram,keys,'tick',pong_tick(ram,keys))
    for index,point in enumerate(table):
        ram=oracle.grow_fixture(point);put8(ram,34,index)
        check('S',ram,0,'tick',oracle.oracle(ram,0,table))
    for _,ram,keys in snake_cases(100):
        put8(ram,34,table.index((ram[7],ram[8])))
        check('S',ram,keys,'tick',oracle.oracle(ram,keys,table))
    for blocked in (1,7,63,64,65):
        ram=[0]*256;put8(ram,34,127)
        for index in range(blocked):set_occupied(ram,table[index],True)
        check('S',ram,0,'food_next_candidate')
    check('S',[10]*256,0,'boot')
    result=dict(status='PASS',**counts,scope='Python original/relocated instructions and independent game oracle; not RTL execution of every fixture')
    out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():raise ValueError('fresh output required')
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);run(p.parse_args().output)
