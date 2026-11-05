#!/usr/bin/env python3
"""Generate relocatable M20 software; no CPU/ISA or original game edits."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'host/python'))
from m20 import assemble
from m20.isa import decode, BRANCHES

# Scratch is separate from Snake ring40..BF / bitmapC0..DF / game00..21.
VARS = dict(HI=0xE0, LO=0xE1, DC=0xE2, SHIFT=0xE3, BITS=0xE4,
            HALF=0xE5, PIX=0xE6, X=0xE7, Y=0xE8, REP=0xE9,
            PAGE=0xEA, COL=0xEB, ROW=0xEC,
            CAND0=0x24, CAND1=0x25, STABLE0=0x26, STABLE1=0x27,
            PREV0=0x28, PREV1=0x29, EDGE0=0x2A, EDGE1=0x2B,
            COUNT=0x2C, MODE=0x2D, SELECT=0x2E, COMBO0=0x2F,
            COMBO1=0x30, COMBO2=0x31, DLY0=0x32, DLY1=0x33,
            RELEASE0=0x34, RELEASE1=0x35, OLDX=0x36, OLDY=0x37,
            OLDL=0x38, OLDR=0x39, TICKS=0x3A, TEMP=0x3B,
            PENDING=0x3C, PLAYKEYS=0x3D, TICKHI=0x3E)


class Program:
    def __init__(self):
        self.lines = [f'.equ {k}, {v}' for k, v in VARS.items()]
        self.calls = {}
        self.counter = 0

    def emit(self, text):
        self.lines.extend(x.strip() for x in text.strip().splitlines())

    def set(self, name, value):
        self.emit(f'LDI {value}\nST {name}')

    def call(self, name):
        index = len(self.calls.setdefault(name, []))
        continuation = f'cont_{self.counter}'
        self.counter += 1
        self.calls[name].append(continuation)
        self.emit(f'@CALL {name} {index}\nJMP {name}\n{continuation}:')

    def ret(self, name):
        self.emit(f'@RETURN {name}')

    def byte(self, value, dc=0):
        self.set('HI', value >> 4)
        self.set('LO', value & 15)
        self.set('DC', 4 if dc else 0)
        self.call('spi')

    def position(self, x, y):
        self.set('X', x)
        self.set('Y', y)

    def finish(self):
        slots = {}
        cursor = 0xED
        for name, sites in self.calls.items():
            if len(sites) > 256:
                raise ValueError(f'{name}: software return ID overflow')
            slots[name] = (cursor, len(sites) > 16)
            cursor += 2 if len(sites) > 16 else 1
        if cursor > 0x100:
            raise ValueError('software continuation RAM overflow')
        result = []
        for line in self.lines:
            if line.startswith('@CALL '):
                _, name, n = line.split(); n = int(n)
                slot, wide = slots[name]
                result.extend([f'LDI {n & 15}', f'ST {slot}'])
                if wide:
                    result.extend([f'LDI {n >> 4}', f'ST {slot+1}'])
            elif line.startswith('@RETURN '):
                name = line.split()[1]; slot, wide = slots[name]
                sites = self.calls[name]
                if wide:
                    for group in range((len(sites) + 15) // 16):
                        result.extend([f'LD {slot+1}', f'SUBI {group}',
                                       f'JZ ret_{name}_{group}'])
                    result.append('HALT')
                for group in range((len(sites) + 15) // 16):
                    result.extend([f'ret_{name}_{group}:', f'LD {slot}'])
                    for n in range(group*16, min(len(sites), (group+1)*16)):
                        if n % 16:
                            result.append('SUBI 1')
                        else:
                            result.append('ANDI 15')
                        result.append(f'JZ {sites[n]}')
                    result.append('HALT')
            else:
                result.append(line)
        return '\n'.join(result) + '\n', slots


def game_source(name, source):
    # Symbolic relocation with the existing assembler, never binary concatenation.
    text = "\n".join(line.split(";",1)[0] for line in source.read_text().splitlines())
    text = re.sub(r'^\s*\.org\s+0\s*$', '', text, flags=re.M)
    symbols = re.findall(r'^\s*(?:\.equ\s+([A-Za-z_]\w*)|([A-Za-z_]\w*):)', text, re.M)
    names = {a or b for a, b in symbols}
    text = re.sub(r'\b[A-Za-z_]\w*\b', lambda m: name+'_'+m[0] if m[0] in names else m[0], text)
    text = text.replace(f'.equ {name}_RETURN_ID,    0xF0', f'.equ {name}_RETURN_ID,    0x3F')
    text = re.sub(rf'(\.equ {name}_RETURN_ID,\s*)0xF0', r'\g<1>0x3F', text)
    text = re.sub(r'\bIN0\b', 'LD PLAYKEYS', text)
    text = re.sub(r'\bIN1\b', 'LD STABLE1', text)
    text = re.sub(rf'{name}_tick_done:\s*NOP\s*JMP {name}_tick',
                  f'{name}_tick_done:\n JMP game_after_tick', text)
    if name == 'S':
        start = text.index('S_boot:')
        end = text.index('S_boot_init:')
        text = text[:start] + '''S_boot:
 ARH 0
 ARL 0
S_clear:
 LDI 0
 ST [AR]
 INCAR
 MOVA ARH
 SUBI 2
 JZ S_clear_low
 SUBI 12
 JZ S_boot_init
 JMP S_clear
S_clear_low:
 MOVA ARL
 SUBI 4
 JZ S_skip_system
 JMP S_clear
S_skip_system:
 ARH 4
 ARL 0
 JMP S_clear
''' + text[end:]
    return text


FONT = {'M':[0x7F,2,12,2,0x7F], '2':[0x62,0x51,0x49,0x49,0x46],
        '0':[0x3E,0x51,0x49,0x45,0x3E], 'P':[0x7F,9,9,9,6],
        'O':[0x3E,0x41,0x41,0x41,0x3E], 'N':[0x7F,2,4,8,0x7F],
        'G':[0x3E,0x41,0x49,0x49,0x7A], 'S':[0x46,0x49,0x49,0x49,0x31],
        'A':[0x7E,9,9,9,0x7E], 'K':[0x7F,8,0x14,0x22,0x41],
        'E':[0x7F,0x49,0x49,0x49,0x41]}


def firmware():
    p = Program()
    p.emit('boot:\n ARH 0\n ARL 0\nclear_ram:\n LDI 0\n ST [AR]\n INCAR\n MOVA ARL\n ANDI 15\n JZ clear_hi\n JMP clear_ram\nclear_hi:\n MOVA ARH\n ANDI 15\n JZ oled_init\n JMP clear_ram\noled_init:')
    # Existing hardware-verified 180 degree orientation; display ON after clear.
    for v in [0xAE,0xD5,0x80,0xA8,0x3F,0xD3,0,0x40,0x8D,0x14,0x20,2,
              0xA0,0xC0,0xDA,0x12,0x81,0x7F,0xD9,0xF1,0xDB,0x40,0xA4,0xA6,0x2E]:
        p.byte(v)
    p.call('clear_screen')
    p.byte(0xAF)
    p.emit('menu_enter:')
    p.set('MODE', 0)
    p.set('STABLE0', 0); p.set('STABLE1', 0)
    for v in ('EDGE0','EDGE1','PENDING','COUNT'):p.set(v,0)
    p.call('clear_screen')
    # Static glyphs are compiled into instructions; no fictional ROM data read.
    for text, y in [('M20',0),('PONG',2),('SNAKE',4)]:
        p.position(2,y); p.call('address')
        for ch in text:
            for b in FONT[ch]+[0]:
                p.byte(b,1)
    p.emit('menu_redraw:')
    # Two selection marks generated as cells, without erasing text.
    p.position(0,2); p.set('PIX',0)
    p.emit('LD SELECT\nJZ mark_pong\nJMP pong_mark_ready\nmark_pong:\nLDI 15\nST PIX\npong_mark_ready:')
    p.call('cell')
    p.position(0,4);p.set('PIX',0)
    p.emit('LD SELECT\nJZ snake_mark_ready\nLDI 15\nST PIX\nsnake_mark_ready:')
    p.call('cell')
    p.emit('menu_loop:');p.call('poll_wait')
    p.emit('LD EDGE0\nST TEMP\nLDI 0\nST EDGE0\nLD TEMP\nANDI 3\nJZ menu_action\nLD SELECT\nXORI 1\nST SELECT\nJMP menu_redraw\nmenu_action:\nLD EDGE1\nST TEMP\nLDI 0\nST EDGE1\nLD TEMP\nANDI 2\nJZ menu_a\nLDI 0\nST SELECT\nJMP menu_redraw\nmenu_a:\nLD TEMP\nANDI 1\nJZ menu_loop')
    p.call('clear_screen')
    p.set('OLDL',15);p.set('OLDR',15)
    p.emit('LD SELECT\nJZ launch_pong\nlaunch_snake:\nLDI 2\nST MODE\nLDI 0\nST PENDING\nST PLAYKEYS\nJMP S_boot\nlaunch_pong:\nLDI 1\nST MODE\nLDI 15\nST OLDL\nST OLDR\nLDI 0\nST PENDING\nST PLAYKEYS\nJMP P_boot\ngame_after_tick:')
    # Redraw a compact whole playfield from CPU state, 16x8 logical cells.
    # Initial implementation measured before selecting optimization.
    p.emit('LD MODE\nSUBI 1\nJZ draw_pong\nJMP draw_snake\ndraw_pong:')
    # Erase previous ball and paddles, redraw current. Idempotent at boot.
    for x,y in [('OLDX','OLDY'),(None,None)]:
        if x:
            p.emit(f'LD {x}\nST X\nLD {y}\nST Y');p.set('PIX',0);p.call('cell')
    for side, old, current in [(0,'OLDL','P_PADDLE_L'),(15,'OLDR','P_PADDLE_R')]:
        p.emit(f'LD {old}\nCMP {current}\nJZ paddle_skip_{side}')
        p.emit(f'LD {old}\nSUBI 15\nJZ paddle_first_{side}')
        p.set('X',side);p.emit(f'LD {old}\nST Y');p.set('PIX',0);p.call('paddle');p.emit(f'paddle_first_{side}:')
        p.set('X',side);p.emit(f'LD {current}\nST Y\nST {old}');p.set('PIX',15);p.call('paddle');p.emit(f'paddle_skip_{side}:')
    p.emit('LD P_BALL_X\nST X\nST OLDX\nLD P_BALL_Y\nST Y\nST OLDY');p.set('PIX',6);p.call('cell')
    # Hexadecimal scores use 3x4 software glyphs in the top row.
    for x,high,low in [(5,'P_SCORE_L_HI','P_SCORE_L_LO'),(10,'P_SCORE_R_HI','P_SCORE_R_LO')]:
        p.position(x,0);p.call('address')
        for value in (high,low):
            p.emit(f'LD {value}\nST PIX');p.call('hex_digit')
    p.emit('JMP game_delay\ndraw_snake:')
    # Render old tail cleared, head/food drawn; the bitmap remains CPU-only.
    p.emit('LD S_EVENT\nANDI 15\nJZ erase_tail\nJMP tail_erased\nerase_tail:\nLD S_OLD_TAIL_X\nST X\nLD S_OLD_TAIL_Y\nST Y');p.set('PIX',0);p.call('cell');p.emit('tail_erased:')
    # On entry (EVENT4), render all three initial segments.
    p.emit('LD S_EVENT\nSUBI 4\nJZ snake_initial\nJMP snake_current\nsnake_initial:')
    for x in [2,3,4]:
        p.position(x,3);p.set('PIX',15);p.call('cell')
    p.emit('snake_current:\nLD S_HEAD_LO\nSHL\nST TEMP\nLD S_HEAD_HI\nADC S_HEAD_HI\nADDI 4\nMOVARH A\nLD TEMP\nMOVARL A\nLD [AR]\nST X\nINCAR\nLD [AR]\nST Y');p.set('PIX',15);p.call('cell')
    p.emit('LD S_FOOD_X\nST X\nLD S_FOOD_Y\nST Y');p.set('PIX',6);p.call('cell')
    p.emit('game_delay:');p.set('TICKS',0);p.set('TICKHI',0)
    p.emit('game_poll:');p.call('poll_wait')
    p.emit('LD EDGE1\nST TEMP\nLDI 0\nST EDGE1\nST EDGE0\nLD TEMP\nANDI 2\nJZ game_a\nJMP menu_enter\ngame_a:\nLD TEMP\nANDI 1\nJZ game_time\nJMP restart_game\ngame_time_jump:\nLD MODE\nSUBI 1\nJZ launch_pong\nJMP launch_snake\ngame_time:\nLD COMBO2\nSUBI 2\nJC menu_enter\nLD TICKS\nADDI 1\nST TICKS\nLD TICKHI\nADCI 0\nST TICKHI\nLD MODE\nSUBI 1\nJZ pong_time\nLD TICKHI\nSUBI 2\nJC snake_time_low\nJMP game_poll\nsnake_time_low:\nLD TICKS\nSUBI 8\nJC game_tick\nJMP game_poll\npong_time:\nLD TICKHI\nSUBI 1\nJC game_tick\nJMP game_poll\ngame_tick:\nLD PENDING\nANDI 15\nJZ use_level\nST PLAYKEYS\nJMP clear_pending\nuse_level:\nLD STABLE0\nST PLAYKEYS\nclear_pending:\nLDI 0\nST PENDING\nLD MODE\nSUBI 1\nJZ P_tick\nJMP S_tick')
    p.emit('restart_game:');p.call('clear_screen');p.emit('JMP game_time_jump')
    # Driver: SPI OUT is the sole source of all four OLED wires.
    p.emit('spi:\n LDI 0\n ST HALF\n LD HI\n ST SHIFT\nspi_half:')
    p.set('BITS',4)
    p.emit('spi_bit:\nLD SHIFT\nANDI 8\nJZ spi_zero\nLDI 1\nJMP spi_level\nspi_zero:\nLDI 0\nspi_level:\nOR DC\nOUT\nADDI 2\nOUT\nSUBI 2\nOUT\nLD SHIFT\nSHL\nST SHIFT\nLD BITS\nSUBI 1\nST BITS\nJZ spi_half_done\nJMP spi_bit\nspi_half_done:\nLD HALF\nANDI 1\nJZ spi_low\nLD DC\nADDI 8\nOUT')
    p.ret('spi')
    p.emit('spi_low:\nLDI 1\nST HALF\nLD LO\nST SHIFT\nJMP spi_half')
    p.emit('address:')
    p.set('HI',11);p.emit('LD Y\nANDI 7\nST LO');p.set('DC',0);p.call('spi')
    p.set('HI',0);p.emit('LD X\nANDI 1\nSHL\nSHL\nSHL\nST LO');p.call('spi')
    p.set('HI',1);p.emit('LD X\nSHR\nST LO');p.call('spi');p.ret('address')
    p.emit('cell:');p.call('address');p.set('REP',8)
    # PIX6 is a true six-pixel plus, not eight copies of0x66.
    # REP8..1 traverses columns [00,00,18,7E,7E,18,00,00].
    p.emit('cell_loop:\nLD PIX\nSUBI 6\nJZ cell_plus\nLD PIX\nST HI\nST LO\nJMP cell_byte\ncell_plus:\nLDI 0\nST HI\nST LO\nLD REP\nSUBI 6\nJZ plus_vertical\nADDI 1\nJZ plus_horizontal\nADDI 1\nJZ plus_horizontal\nADDI 1\nJZ plus_vertical\nJMP cell_byte\nplus_vertical:\nLDI 1\nST HI\nLDI 8\nST LO\nJMP cell_byte\nplus_horizontal:\nLDI 7\nST HI\nLDI 14\nST LO\ncell_byte:');p.set('DC',4);p.call('spi')
    p.emit('LD REP\nSUBI 1\nST REP\nJZ cell_done\nJMP cell_loop\ncell_done:');p.call('poll_keys');p.ret('cell')
    p.emit('paddle:');p.emit('LD Y\nST ROW');p.call('cell')
    p.emit('LD ROW\nADDI 1\nST Y');p.call('cell')
    p.emit('LD ROW\nADDI 2\nST Y');p.call('cell');p.ret('paddle')
    p.emit('clear_screen:');p.set('PAGE',0)
    p.emit('clear_page:\nLD PAGE\nST Y');p.set('X',0);p.call('address');p.set('COL',0)
    p.emit('clear_cell:');p.set('REP',8)
    p.emit('clear_byte:');p.byte(0,1)
    p.emit('LD REP\nSUBI 1\nST REP\nJZ clear_next\nJMP clear_byte\nclear_next:');p.call('poll_keys');p.emit('LD COL\nADDI 1\nST COL\nJZ clear_next_page\nJMP clear_cell\nclear_next_page:\nLD PAGE\nADDI 1\nST PAGE\nSUBI 8\nJZ clear_done\nJMP clear_page\nclear_done:');p.ret('clear_screen')
    # Software delay: 4 nested nibble counts, ~a few ms at1MHz, measured later.
    p.emit('poll_wait:');p.set('DLY0',0);p.set('DLY1',0)
    p.emit('wait_inner:\nLD DLY0\nADDI 1\nST DLY0\nJZ wait_hi\nJMP wait_inner\nwait_hi:\nLD DLY1\nADDI 1\nST DLY1\nJZ wait_done\nJMP wait_inner\nwait_done:')
    p.call('poll_keys')
    p.emit('LD STABLE0\nANDI 3\nSUBI 3\nJZ combo_count\nLDI 0\nST COMBO0\nST COMBO1\nST COMBO2\nJMP poll_done\ncombo_count:\nLD COMBO2\nSUBI 2\nJC poll_done\nLD COMBO0\nADDI 1\nST COMBO0\nLD COMBO1\nADCI 0\nST COMBO1\nLD COMBO2\nADCI 0\nST COMBO2\npoll_done:');p.ret('poll_wait')
    # All glyph constants are instruction immediates, never an FPGA/font ROM.
    p.emit('hex_digit:');p.set('HI',0);p.set('DC',4)
    for value in range(16):p.emit(f'LD PIX\nSUBI {value}\nJZ hex_{value}')
    p.emit('HALT')
    glyphs=[(15,9,15),(0,15,0),(13,11,0),(9,11,15),(7,4,15),(11,9,13),
            (15,9,13),(1,1,15),(15,11,15),(7,5,15),(15,5,15),(15,10,14),
            (15,9,9),(15,9,6),(15,11,9),(15,3,1)]
    for value,columns in enumerate(glyphs):
        p.emit(f'hex_{value}:')
        for column in columns:
            p.set('LO',column);p.call('spi')
        p.emit('JMP hex_return')
    p.emit('hex_return:');p.set('LO',0);p.call('spi');p.ret('hex_digit')
    p.emit('poll_keys:')
    # Whole six-bit stable state: 3 consecutive equal samples, no FPGA debounce.
    p.emit('LD STABLE0\nST PREV0\nLD STABLE1\nST PREV1\nIN0\nST TEMP\nCMP CAND0\nJZ poll_bank1\nST CAND0\nLDI 0\nST COUNT\npoll_bank1:\nIN1\nST TEMP\nCMP CAND1\nJZ poll_equal\nST CAND1\nLDI 0\nST COUNT\npoll_equal:\nLD COUNT\nSUBI 3\nJC poll_edges\nLD COUNT\nADDI 1\nST COUNT\nSUBI 3\nJZ accept_keys\nJMP poll_edges\naccept_keys:\nLD CAND0\nST STABLE0\nLD CAND1\nST STABLE1\npoll_edges:\nLD STABLE0\nNOT\nAND PREV0\nST RELEASE0\nLD STABLE1\nNOT\nAND PREV1\nST RELEASE1\nLD PREV0\nNOT\nAND STABLE0\nOR EDGE0\nST EDGE0\nLD PREV1\nNOT\nAND STABLE1\nOR EDGE1\nST EDGE1\nLD STABLE0\nCMP PREV0\nJZ keys_done\nLD STABLE0\nANDI 15\nJZ keys_done\nST PENDING\nkeys_done:');p.ret('poll_keys')
    p.emit(game_source('P',ROOT/'software/m20_300/pong.asm'))
    p.emit(game_source('S',ROOT/'software/m20_300/variants/snake_shuffled_v0_1/snake_shuffled.asm'))
    source, slots = p.finish()
    image = assemble(source,'m20_v31.asm')
    for row in image.listing:
        ins = decode(row['word'])
        if ins.mnemonic in BRANCHES and ins.operand not in image.source_map:
            raise ValueError(f"jump outside emitted program at {row['address']}")
    meta = dict(version='M20-V31-0.2',words=len(image.words),free_words=4096-len(image.words),
                isa='M20-300-ISA-0.1',cpu_mode='FUNCTIONAL_STORAGE',
                ram_variables=VARS,return_slots=slots,return_sites={k:len(v) for k,v in p.calls.items()},
                symbols=image.symbols,original_games_unchanged=True,
                snake_food='V3 fixed shuffled128 table; CPU skip occupied preserved',
                source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                rom_sha256=hashlib.sha256(image.memh.encode()).hexdigest())
    return source,image,meta


def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--output',type=Path,required=True)
    out=a.parse_args().output
    if out.exists():raise SystemExit('Choose a fresh firmware output directory')
    source,image,meta=firmware();out.mkdir(parents=True)
    (out/'m20_v31.asm').write_text(source)
    (out/'m20_v31.memh').write_text(image.memh)
    (out/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps({k:meta[k] for k in ('version','words','free_words','return_sites')}))


if __name__=='__main__':main()
