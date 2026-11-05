#!/usr/bin/env python3
"""Independent CPU-OUT SPI decoder, GDDRAM oracle and software scenarios."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'host/python'))
sys.path.insert(0,str(Path(__file__).parent))
from build_firmware import firmware,VARS
from m20.machine import Machine


class OLED:
    def __init__(self):
        self.gpo=8; self.bits=[];self.bytes=[];self.ram=[None]*1024
        self.page=0;self.column=0;self.pending=None;self.on=False
        self.last_edge=0;self.last_data=0;self.minimum_setup=10**20
        self.bit_periods=[];self.high_periods=[];self.rise=0

    def out(self,value,cycles,pc):
        old=self.gpo;self.gpo=value
        if (old^value)&1:self.last_data=cycles
        if old&8 and not value&8:
            assert not value&2,'CS asserted with SCK high'
            self.bits=[];self.dc=bool(value&4)
        if not value&8:
            assert bool(value&4)==self.dc,'DC changed within byte'
            if not old&2 and value&2:
                self.minimum_setup=min(self.minimum_setup,cycles-self.last_data)
                assert cycles-self.last_data>=2,'no MOSI setup'
                if self.bits:self.bit_periods.append(cycles-self.rise)
                self.rise=cycles
                self.bits.append(value&1)
                self.last_edge=cycles
        if old&2 and not value&2 and not old&8:self.high_periods.append(cycles-self.rise)
        if not old&8 and value&8:
            assert not value&2 and len(self.bits)==8,(pc,len(self.bits))
            byte=0
            for bit in self.bits:byte=(byte<<1)|bit
            self.bytes.append(dict(cycles=cycles,pc=pc,dc=int(self.dc),value=byte))
            if self.dc:
                assert 0<=self.page<8 and 0<=self.column<128
                self.ram[self.page*128+self.column]=byte
                self.column+=1
            elif self.pending:
                if self.pending==0x20:assert byte==2
                self.pending=None
            elif byte in (0xd5,0xa8,0xd3,0x8d,0x20,0xda,0x81,0xd9,0xdb):self.pending=byte
            elif 0xb0<=byte<=0xb7:self.page=byte&7
            elif byte<16:self.column=(self.column&0xf0)|byte
            elif 0x10<=byte<=0x1f:self.column=(self.column&15)|((byte&15)<<4)
            elif byte==0xaf:
                assert self.ram==[0]*1024,'display enabled before clean GDDRAM'
                self.on=True


class Runner:
    def __init__(self):
        self.source,self.image,self.meta=firmware()
        self.cpu=Machine(self.image.words,trace=False,ram=[15]*256)
        self.oled=OLED();self.inputs=[];self.frames=[];self.events=[];self.vector_file=None;self.timing=[];self.draw_start=None

    def step(self):
        m=self.cpu;keys=m.keys
        if m.pc==self.image.symbols['game_after_tick']:self.draw_start=(m.cycles,m.retired)
        if m.pc==self.image.symbols['game_poll'] and self.draw_start is not None:
            self.timing.append(dict(mode=m.ram[VARS['MODE']],phase='draw',microcycles=m.cycles-self.draw_start[0],instructions=m.retired-self.draw_start[1]))
            self.draw_start=None
        e=m.step()
        if self.vector_file:
            value=e['pc']
            for field,width in [(e['word'],16),(m.pc,12),(m.ar,8),(m.a,4),(m.z,1),(m.c,1),(m.gpo,4),(keys,6)]:
                value=(value<<width)|field
            self.vector_file.write(f'{value:016X}\n')
        assert e and m.status=='RUNNING',(m.pc,m.status)
        if e['gpio'] is not None:self.oled.out(e['gpio'],m.cycles,e['pc'])
        if e['input'] is not None:self.inputs.append(m.cycles)
        return e

    def until(self,label,limit=1500000):
        target=self.image.symbols[label]
        for _ in range(limit):
            if self.cpu.pc==target:return
            self.step()
        raise AssertionError(f'timeout {label}: {self.cpu.pc}')

    def visit(self,label,keys=0):
        self.cpu.keys=keys;self.step();self.until(label)

    def menu_poll(self,keys):
        self.visit('menu_loop',keys)

    def boot(self):
        self.until('menu_loop')
        assert self.oled.on
        assert self.cpu.ram[VARS['MODE']]==0

    def press(self,mask):
        for _ in range(4):self.menu_poll(mask)

    def select(self,game):
        # Drive six-key levels; never force PC, RAM or software states.
        if game=='snake':
            self.press(2);self.press(0)
            assert self.cpu.ram[VARS['SELECT']]==1
        self.cpu.keys=16
        for _ in range(1500000):
            if self.cpu.pc==self.image.symbols['game_poll']:return
            self.step()
        raise AssertionError('A did not launch game')

    def tick(self):
        self.until('game_after_tick')
        self.step();self.until('game_poll')

    def check_pixels(self,game):
        ram=self.cpu.ram
        if game=='snake':
            for y in range(8):
                for x in range(16):
                    occupied=bool(ram[0xC0+4*y+x//4]&(1<<(x%4)))
                    expected=[255]*8 if occupied else [0,0,24,126,126,24,0,0] if (x,y)==(ram[7],ram[8]) else [0]*8
                    actual=self.oled.ram[y*128+x*8:y*128+x*8+8]
                    assert actual==expected,('snake pixel',x,y,actual,expected)
        else:
            for x,top in [(0,ram[4]),(15,ram[5])]:
                for y in range(8):
                    expected=255 if top<=y<top+3 else 0
                    assert self.oled.ram[y*128+x*8:y*128+x*8+8]==[expected]*8,('paddle',x,y)
            x,y=ram[0],ram[1]
            if y!=0 or x not in (5,10):
                assert self.oled.ram[y*128+x*8:y*128+x*8+8]==[0,0,24,126,126,24,0,0]


def validate(out,vectors=False):
    out.mkdir(parents=True,exist_ok=False)
    r=Runner()
    if vectors:r.vector_file=(out/'vectors.hex').open('w')
    r.boot();boot=r.cpu.cycles
    screens={'menu':list(r.oled.ram)}
    # Glitches separated by releases never reach a stable press.
    for k in [2,0,2,0,2,0]:r.menu_poll(k)
    assert r.cpu.ram[VARS['SELECT']]==0
    r.press(2);assert r.cpu.ram[VARS['SELECT']]==1
    r.press(2);assert r.cpu.ram[VARS['SELECT']]==1,'held key repeated'
    r.press(0);r.press(1);assert r.cpu.ram[VARS['SELECT']]==0
    r.press(0)
    r.select('pong')
    r.cpu.keys=0
    pcycles=[];pinput_start=len(r.inputs)
    r.check_pixels('pong')
    for _ in range(6):
        start=r.cpu.cycles;r.tick();pcycles.append(r.cpu.cycles-start)
        assert 1<=r.cpu.ram[0]<=14 and r.cpu.ram[1]<=7
        r.check_pixels('pong')
    # Real A edges after release; stale old positions must not hide the
    # stationary paddles after the software clear. No forced PC/state.
    for _ in range(2):
        for _ in range(4):r.visit('game_poll',0)
        r.cpu.keys=16;r.until('restart_game');r.step();r.until('game_poll')
        r.check_pixels('pong')
    # B returns to software menu, no CPU reset / bank-select.
    screens['pong']=list(r.oled.ram)
    pinputs=r.inputs[pinput_start:]
    r.cpu.keys=32;r.until('menu_enter');r.cpu.keys=0;r.step();r.until('menu_loop')
    r.press(0);r.select('snake');r.cpu.keys=0
    scycles=[];sinput_start=len(r.inputs)
    r.check_pixels('snake')
    for _ in range(4):
        start=r.cpu.cycles;r.tick();scycles.append(r.cpu.cycles-start)
        assert r.cpu.ram[4]>=3
        r.check_pixels('snake')
    screens['snake']=list(r.oled.ram)
    sinputs=r.inputs[sinput_start:]
    r.cpu.keys=32;r.until('menu_enter');r.cpu.keys=0;r.step();r.until('menu_loop')
    r.cpu.keys=0
    # SRAM is never assumed reset zero; boot was explicitly tested from allF.
    if r.vector_file:r.vector_file.close()
    (out/'final_ram.memh').write_text(''.join(f'{n:X}\n' for n in r.cpu.ram))
    (out/'gddram_screens.json').write_text(json.dumps(screens)+'\n')
    with (out/'drawing_cycles.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=['mode','phase','microcycles','instructions']);w.writeheader();w.writerows(r.timing)
    bytes_path=out/'spi_bytes.csv'
    with bytes_path.open('w') as f:
        w=csv.DictWriter(f,fieldnames=['cycles','pc','dc','value']);w.writeheader();w.writerows(r.oled.bytes)
    periods=[b-a for a,b in zip(r.inputs,r.inputs[1:]) if b>a]
    result=dict(status='PASS',words=len(r.image.words),free_words=4096-len(r.image.words),
                cpu_micro_hz=1000000,boot_cycles=boot,boot_seconds=boot/1e6,
                pong_frame_cycles=pcycles,snake_frame_cycles=scycles,
                maximum_input_gap_cycles=max(periods),
                pong_input_gap_cycles=max(b-a for a,b in zip(pinputs,pinputs[1:])),
                snake_input_gap_cycles=max(b-a for a,b in zip(sinputs,sinputs[1:])),minimum_spi_setup_cycles=r.oled.minimum_setup,
                spi_bytes=len(r.oled.bytes),
                intra_byte_spi_period_cycles=[min(r.oled.bit_periods),max(r.oled.bit_periods)],
                spi_high_cycles=[min(r.oled.high_periods),max(r.oled.high_periods)],executed_instructions=r.cpu.retired,
                pong_A_restart_checks=2,plus_glyph_columns=[0,0,24,126,126,24,0,0],
                scenario='boot allF RAM, glitch/held/release/menu, repeated Pong A restart, plus pixels, both games, B return',
                physical_hardware='NOT_RUN')
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);a.add_argument('--vectors',action='store_true')
    args=a.parse_args();validate(args.output,args.vectors)
