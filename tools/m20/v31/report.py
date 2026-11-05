#!/usr/bin/env python3
"""Regenerate small V3.1 ROM/performance/GDDRAM report artifacts offline."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(Path(__file__).parent))
from build_firmware import firmware


def report(software,implementation,out):
    out.mkdir(parents=True,exist_ok=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    source,image,meta=firmware()
    verification=json.loads((software/'verification.json').read_text())
    assert verification['words']==len(image.words)
    routed=json.loads((implementation/'route_audit/counts.json').read_text())
    assert routed['mux_lut3']==477 and routed['cpu_native_ff']==33
    timing=(implementation/'timing.rpt').read_text()
    m=re.search(r'\n\s*([-\d.]+)\s+([-\d.]+)\s+\d+\s+\d+\s+([-\d.]+)\s+([-\d.]+)\s+\d+\s+\d+\s+([-\d.]+)',timing)
    if not m:raise ValueError('missing timing summary')
    sta=dict(wns_ns=float(m[1]),tns_ns=float(m[2]),whs_ns=float(m[3]),ths_ns=float(m[4]),wpws_ns=float(m[5]))
    assert sta['wns_ns']>=0 and sta['whs_ns']>=0
    symbols=meta['symbols'];segments=[]
    boundaries=['boot','menu_enter','spi','address','cell','paddle','clear_screen','poll_wait','hex_digit','poll_keys','P_boot','S_boot']
    for i,name in enumerate(boundaries):
        start=symbols[name];end=symbols[boundaries[i+1]] if i+1<len(boundaries) else len(image.words)
        assert end>=start
        segments.append(dict(section=name,start=start,end_exclusive=end,words=end-start))
    with (out/'rom_layout.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['section','start','end_exclusive','words']);w.writeheader();w.writerows(segments)
    for name in ['verification.json','drawing_cycles.csv']:
        shutil.copyfile(software/name,out/name)
    fig,ax=plt.subplots(figsize=(8,3),layout='constrained')
    for y,(game,color) in enumerate([('pong','steelblue'),('snake','seagreen')]):
        values=verification[game+'_frame_cycles']
        ax.barh(y,np.mean(values)/1000,color=color,label=game.upper())
        ax.text(np.mean(values)/1000+2,y,f'{1e6/np.mean(values):.2f} Hz',va='center')
    ax.set_yticks([0,1],['Pong','Snake']);ax.set_xlabel('CPU software frame interval (ms), microcycle = 1 MHz')
    ax.set_xlim(0,250);ax.set_title('Python instruction execution, including software SPI and polling')
    fig.savefig(out/'frame_budget.svg');plt.close(fig)
    screens=json.loads((software/'gddram_screens.json').read_text())
    fig,axes=plt.subplots(1,3,figsize=(12,2.7),layout='constrained')
    for ax,(name,ram) in zip(axes,screens.items()):
        bitmap=np.array([[bool(ram[(y//8)*128+x]&(1<<(y%8))) for x in range(128)] for y in range(64)])
        ax.imshow(bitmap,cmap='gray',interpolation='nearest',vmin=0,vmax=1)
        ax.set_title(name);ax.axis('off')
    fig.suptitle('GDDRAM reconstructed exclusively from CPU OUT software SPI (simulation)')
    fig.savefig(out/'software_oled.png',dpi=160);plt.close(fig)
    summary=dict(status='DIGITAL_PASS_HARDWARE_PENDING',firmware_words=len(image.words),free_words=4096-len(image.words),
                 isa_unchanged=True,mode='FUNCTIONAL_STORAGE',cpu=routed,sta=sta,
                 source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                 rom_sha256=hashlib.sha256(image.memh.encode()).hexdigest(),
                 bitstream_sha256=hashlib.sha256((implementation/'swcell_m20_v31_top.bit').read_bytes()).hexdigest(),
                 inputs=dict(software=str(software),implementation=str(implementation)),
                 measurement_scope='software instruction simulation and FPGA route STA; not physical157 or OLED hardware acceptance')
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--software',type=Path,required=True);a.add_argument('--implementation',type=Path,required=True);a.add_argument('--output',type=Path,required=True)
    args=a.parse_args();report(args.software,args.implementation,args.output)
