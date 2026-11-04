#!/usr/bin/env python3
"""Reproduce repeated scoring/center serve with the frozen Pong ROM; no ROM edits."""
import argparse
import csv
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'host/python'))
from m20 import Machine,assemble
from m20.game_reference import pong_initial,pong_tick,PONG_FIELDS

def review(out):
    out.mkdir(parents=True,exist_ok=False)
    asm=assemble((ROOT/'software/m20_300/pong.asm').read_text())
    witnesses={};checked=0
    for left in range(6):
        for right in range(6):
            initial=pong_initial();initial[4:6]=[left,right]
            m=Machine(asm.words,ram=initial,pc=asm.symbols['tick'],trace=False)
            rows=[]
            for tick in range(1,129):
                expected=pong_tick(m.ram,0)
                for _ in range(1000):
                    if m.pc==asm.symbols['tick_done']:break
                    assert m.step() is not None
                else:raise RuntimeError('ROM did not finish tick')
                assert all(m.ram[i]==expected[i] for i in PONG_FIELDS),(left,right,tick)
                rows.append(dict(tick=tick,x=m.ram[0],y=m.ram[1],vx=m.ram[2],vy=m.ram[3],left=left,right=right,
                                 score_l=m.ram[6]+16*m.ram[7],score_r=m.ram[8]+16*m.ram[9],event=m.ram[10]))
                checked+=1;m.step() # genuine tick_done NOP before next loop
            if left==2 and right in (2,5):witnesses[right]=rows
    for right,rows in witnesses.items():
        with (out/f'right_paddle_{right}.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    assert [r['tick'] for r in witnesses[5] if r['event']==4][:4]==[7,14,21,28]
    result=dict(status='PASS',source='frozen Pong machine code executed by Python ISA Machine; independent mathematical rule comparison',
                paddle_configurations=36,ticks_per_configuration=128,checked_ticks=checked,
                witness='right paddle top5 covers y5..7; fixed serve contacts at new y3, so miss/scoring repeats each7ticks',
                original_rom_changed=False,hardware_claim=False)
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(2,1,figsize=(8,4.5),sharex=True,layout='constrained')
    for right,rows in witnesses.items():
        rows=rows[:42];label=f'Right paddle top={right}'
        ax[0].plot([r['tick'] for r in rows],[r['x'] for r in rows],'.-',label=label)
        ax[1].step([r['tick'] for r in rows],[r['score_l'] for r in rows],where='post',label=label)
    ax[0].set_ylabel('Ball X (cell)');ax[0].set_ylim(0,15);ax[0].legend()
    ax[1].set_ylabel('Left score');ax[1].set_xlabel('CPU game tick')
    for a in ax:a.grid(alpha=.25)
    fig.suptitle('Frozen Pong ROM: bounce versus repeated miss/serve (software oracle)')
    fig.savefig(out/'bounce_vs_repeated_serve.png',dpi=140);plt.close(fig)
    print('M20_V3_PONG_SERVE_REVIEW_PASS',json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);review(p.parse_args().output)
