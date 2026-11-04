#!/usr/bin/env python3
"""Generate a separately versioned, CPU-executed fixed-permutation Snake ROM."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'host/python'))
from m20 import assemble

def generate(out):
    if out.exists():raise ValueError('use a fresh variant directory')
    prefix=[(10,3),(2,6),(13,1),(5,5),(1,0),(14,7),(7,2),(11,6),(3,4),(15,1),(0,7),(8,0)]
    remaining=[(x,y) for y in range(8) for x in range(16) if (x,y) not in prefix]
    random.Random(0x20F004).shuffle(remaining);table=prefix+remaining
    assert len(table)==len(set(table))==128
    original=ROOT/'software/m20_300/snake.asm';source=original.read_text()
    source=source.replace('.equ RETURN_ID, 0xF0','.equ FOOD_SEQ_LO, 0x22\n.equ FOOD_SEQ_HI, 0x23\n.equ RETURN_ID, 0xF0')
    start=source.index('    ; Search starts at old_food+1')
    end=source.index('    LD PROBES_LO',start)
    source=source[:start]+'''    ; Variant: cyclic fixed 128-position permutation, interpreted by CPU only.
food_next_candidate:
    LD FOOD_SEQ_LO
    ADDI 1
    ST FOOD_SEQ_LO
    LD FOOD_SEQ_HI
    ADCI 0
    ANDI 7
    ST FOOD_SEQ_HI
    JMP food_table_dispatch
food_table_return:
'''+source[end:]
    blocks=['','; Code table: ISA has no data load from ROM. Branches select constants.','food_table_dispatch:','    LD FOOD_SEQ_HI']
    for hi in range(8):blocks += [f'    SUBI {0 if hi==0 else 1}',f'    JZ food_table_hi_{hi}']
    blocks+=['    JMP bitmap_fault']
    for hi in range(8):
        blocks += [f'food_table_hi_{hi}:','    LD FOOD_SEQ_LO']
        for lo in range(16):blocks += [f'    SUBI {0 if lo==0 else 1}',f'    JZ food_entry_{hi*16+lo}']
        blocks+=['    JMP bitmap_fault']
    for index,(x,y) in enumerate(table):
        blocks += [f'food_entry_{index}:',f'    LDI {x}','    ST LOOK_X',f'    LDI {y}','    ST LOOK_Y','    JMP food_table_return']
    source+='\n'.join(blocks)+'\n'
    program=assemble(source)
    assert len(program.words)<4096
    out.mkdir(parents=True)
    (out/'snake_shuffled.asm').write_text(source)
    (out/'snake_shuffled.memh').write_text(program.memh+'FFFF\n'*(4096-len(program.words)))
    (out/'food_table.json').write_text(json.dumps(dict(version='SNAKE-SHUFFLED-0.1',positions=table,initial_index=0,
        runtime='fixed cyclic permutation, not random',index_ram=[34,35],max_probe_limit=65),indent=2)+'\n')
    manifest=dict(version='SNAKE-SHUFFLED-0.1',original_source=str(original.relative_to(ROOT)),
                  original_source_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
                  words=len(program.words),rom_capacity_words=4096,tick=program.symbols['tick'],tick_done=program.symbols['tick_done'],
                  source='snake_shuffled.asm',rom='snake_shuffled.memh',table='food_table.json',
                  rom_sha256=hashlib.sha256((out/'snake_shuffled.memh').read_bytes()).hexdigest(),
                  cpu_isa_unchanged=True,cpu_state_bits=33,additional_software_ram_nibbles=2,
                  implementation='CPU branches select ROM-encoded constants; original bitmap lookup skips occupied entries')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);generate(p.parse_args().output)
