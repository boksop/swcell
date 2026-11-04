#!/usr/bin/env python3
"""Compare captured FPGA-adapter RAM snapshots with the independent ISA machine."""
import argparse
import csv
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'host/python'))
from m20 import Machine,assemble

def verify(path):
    rows=list(csv.DictReader(path.open()))
    result={}
    for game,name in enumerate(('pong','snake')):
        asm=assemble((ROOT/f'software/m20_300/{name}.asm').read_text())
        machine=Machine(asm.words,trace=False)
        selected=[r for r in rows if int(r['game'])==game][:64]
        if len(selected)!=64:raise ValueError(f'{name}: missing 64 frames')
        for index,row in enumerate(selected):
            if index:machine.step() # Execute the genuine tick_done NOP before resuming.
            for _ in range(20000):
                if machine.pc==asm.symbols['tick_done']:break
                event=machine.step()
                if not event or machine.status!='RUNNING':raise ValueError('unexpected terminal state')
            else:raise ValueError('tick exceeded bound')
            ram=[int(c,16) for c in row['ram_descending'].strip()][::-1]
            if ram!=machine.ram:
                difference=[(i,a,b) for i,(a,b) in enumerate(zip(ram,machine.ram)) if a!=b]
                raise ValueError(f'{name} tick {index} mismatches {difference[:10]}')
        result[name]=dict(frames=64,ram_cells_per_frame=256,final_cpu_cycles=machine.cycles,retired=machine.retired)
    return dict(status='PASS',reference='independent Python ISA Machine; original ROM; zero keys',games=result)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('csv',type=Path);a=p.parse_args()
    result=verify(a.csv);a.csv.with_suffix('.verification.json').write_text(json.dumps(result,indent=2)+'\n');print('M20_V3_FRAME_ORACLE_PASS',json.dumps(result))
