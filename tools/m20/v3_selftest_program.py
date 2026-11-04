#!/usr/bin/env python3
"""Additional CPU-executed diagnostic ROM. Does not modify either original game."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'host/python'))
from m20 import Machine,assemble

def generate(out):
    out.mkdir(parents=True,exist_ok=False)
    lines=['; V3 hardware instruction-family exercise; all results written by CPU.',
           'LD 0xF7','JZ tests','LDI 12','OUT','JMP 141','.org 141','NOP','HALT','.org 512','tests:']
    scenarios=[];address=0
    operations=[f'{op} 1' for op in ('LDI','ADDI','ADCI','SUBI','SBCI','ANDI','XORI')]+['SHL','SHR','NOT']
    operations += [f'{op} {addr}' for addr in ('0xF8','[AR]') for op in ('LD','ST','ADD','ADC','SUB','SBC','CMP','AND','XOR','OR')]
    for index,op in enumerate(operations):
        for carry in (0,1):
            lines+=['LDI 3','ST 0xF8','ARL 8','ARH 15',
                    'LDI 15' if carry else 'LDI 0','ADDI 1' if carry else 'ADDI 0','LDI 15',op]
            tag=f't{index}_{carry}';base=address
            lines += [f'ST {address}',f'JZ {tag}_z1','LDI 0',f'JMP {tag}_zsave',f'{tag}_z1:','LDI 1',
                      f'{tag}_zsave:',f'ST {address+1}',f'JC {tag}_c1','LDI 0',f'JMP {tag}_csave',f'{tag}_c1:','LDI 1',
                      f'{tag}_csave:',f'ST {address+2}']
            address+=3;scenarios.append(dict(operation=op,carry_in=carry,a_before=15,result_addresses=[base,base+1,base+2]))
    for index,op in enumerate(('ARL 7','ARH 2','MOVARL A','MOVARH A','MOVA ARL','MOVA ARH','INCAR','IN0','IN1','OUT','NOP')):
        lines+=['ARL 15','ARH 15','LDI 5',op,f'ST {address}','MOVA ARL',f'ST {address+1}','MOVA ARH',f'ST {address+2}']
        scenarios.append(dict(operation=op,result_addresses=list(range(address,address+3))))
        address+=3
    assert address<247
    lines += ['LDI 1','ST 0xF7','JMP 4095','.org 4095','NOP']
    source='\n'.join(lines)+'\n';asm=assemble(source)
    m=Machine(asm.words,keys=0,trace=False);m.run(max_instructions=10000)
    assert m.halted and m.gpo==12
    (out/'isa_selftest.asm').write_text(source)
    (out/'isa_selftest.memh').write_text(asm.memh)
    (out/'illegal.memh').write_text('0010\n'+'FFFF\n'*4095)
    expected=dict(status='HALTED',ram=m.ram,registers=m.registers,retired=m.retired,cycles=m.cycles,
                  ram_writes=m.ram_writes,ram_reads=m.ram_reads,scenarios=scenarios,
                  coverage='all ISA operation families; both RAM addressing modes; both input carry states; PC/AR wrap; branches/flags/IN/OUT/HALT',
                  limits='finite operand vectors, zero input keys; not all 15015 legal encodings or all operand combinations')
    (out/'expected.json').write_text(json.dumps(expected,indent=2)+'\n')
    print('M20_V3_SELFTEST_ROM',len(scenarios),'vectors',m.retired,'instructions',m.cycles,'microcycles')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);generate(p.parse_args().output)
