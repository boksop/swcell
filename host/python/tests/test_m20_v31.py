import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/m20/v31'))
from build_firmware import firmware,VARS,Program
from verify_firmware import Runner,OLED
from m20 import assemble
from m20.machine import Machine


class M20V31Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.source,cls.image,cls.meta=firmware()

    def test_frozen_v3_and_cpu_bytes(self):
        for name,digest in json.loads((ROOT/'docs/m20/v31_resources/baseline_sha256.json').read_text()).items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest,name)

    def test_firmware_reproducibility_capacity_and_jump_targets(self):
        self.assertEqual(self.source,(ROOT/'software/m20_300/v31/m20_v31.asm').read_text())
        self.assertEqual(self.image.memh,(ROOT/'software/m20_300/v31/m20_v31.memh').read_text())
        self.assertLessEqual(len(self.image.words),4096)
        from m20.isa import decode,BRANCHES
        for row in self.image.listing:
            ins=decode(row['word'])
            if ins.mnemonic in BRANCHES:self.assertIn(ins.operand,self.image.source_map)

    def test_software_call_id_does_not_wrap(self):
        p=Program()
        for _ in range(257):p.call('overflow')
        p.ret('overflow')
        with self.assertRaises(ValueError):p.finish()

    def test_boot_from_dirty_ram_and_bounce_single_action(self):
        r=Runner();r.boot()
        for k in (2,0,2,0,2,0):r.menu_poll(k)
        self.assertEqual(r.cpu.ram[VARS['SELECT']],0)
        r.press(2);self.assertEqual(r.cpu.ram[VARS['SELECT']],1)
        r.press(2);self.assertEqual(r.cpu.ram[VARS['SELECT']],1)
        r.press(0);r.press(1);self.assertEqual(r.cpu.ram[VARS['SELECT']],0)

    def test_relocated_games_match_original_cpu_algorithms(self):
        # Software boundaries only; no forced execution state in real RTL.
        for game,original in [('P','software/m20_300/pong.asm'),
                              ('S','software/m20_300/variants/snake_shuffled_v0_1/snake_shuffled.asm')]:
            source=assemble((ROOT/original).read_text())
            ref=Machine(source.words,trace=False)
            new=Machine(self.image.words,pc=self.image.symbols[game+'_boot'],trace=False)
            new.ram[VARS['MODE']]=1 if game=='P' else 2
            # Symbolic boot performs all game initialization. IO/driver is outside.
            for tick in range(16):
                if tick:
                    keys=(1,2,4,8,0)[tick%5]
                    ref.keys=keys;new.ram[VARS['PLAYKEYS']]=keys;new.ram[VARS['STABLE1']]=0
                    ref.step();new.pc=self.image.symbols[game+'_tick']
                ref.run(20000,stop_pc=source.symbols['tick_done'])
                new.run(20000,stop_pc=self.image.symbols[game+'_tick_done'])
                self.assertEqual(ref.status,'RUNNING');self.assertEqual(new.status,'RUNNING')
                region=range(0x21 if game=='P' else 0x24)
                for a in region:self.assertEqual(new.ram[a],ref.ram[a],(game,tick,a))
                if game=='S':self.assertEqual(new.ram[0x40:0xE0],ref.ram[0x40:0xE0])

    def test_spi_receiver_detects_invalid_bit_count(self):
        p=OLED();p.out(0,0,0);p.out(2,4,1);p.out(0,8,2)
        with self.assertRaises(AssertionError):p.out(8,12,3)

    def test_cpu_release_and_long_combo_return_without_reset(self):
        r=Runner();r.boot();r.press(2)
        for _ in range(3):r.menu_poll(0)
        self.assertEqual(r.cpu.ram[VARS['RELEASE0']],2)
        self.assertEqual(r.cpu.ram[VARS['STABLE0']],0)
        # Return selection to Pong through real CPU menu instructions.
        r.press(1);r.press(0);r.select('pong');r.cpu.keys=3
        start=r.cpu.cycles;retired=r.cpu.retired
        r.until('menu_enter',limit=3000000)
        self.assertEqual(r.cpu.ram[VARS['COMBO2']],2)
        self.assertGreater(r.cpu.retired,retired)
        # CPU software long press, including drawing time, near3 seconds.
        self.assertGreater(r.cpu.cycles-start,2000000)
        self.assertLess(r.cpu.cycles-start,4000000)

    def test_v31_uart_format_and_reserved_bits(self):
        import swcell_m20_v31 as uart
        row={k:'0'*n for k,n in uart.WIDTHS.items()}
        row.update(type='M20_V31_STATE',build='M20V31A01',keys='3F',writes='FFFFFFFFFFFFFFFF')
        decoded=uart.parse_record(json.dumps(row))
        self.assertEqual(decoded['keys'],63);self.assertEqual(decoded['writes'],2**64-1)
        for change in ({'keys':'40'},{'flags':'80'},{'pc':'0'},{'type':'M20_V3_STATE'}):
            with self.assertRaises(ValueError):uart.parse_record(json.dumps(row|change))

    def test_platform_has_no_game_or_oled_hardware_bypass(self):
        base=ROOT/'rtl/modules/m20/v31'
        service=(base/'swc_m20_v31_service.sv').read_text()
        for forbidden in ('TICK_DONE','wait_tick','frame_ram','snapshot','select_game','PONG','SNAKE'):
            self.assertNotIn(forbidden,service)
        top=(ROOT/'fpga/projects/m20/autonomous/rtl/swcell_m20_v31_top.sv').read_text()
        for forbidden in ('swc_ssd1306','swc_spi_tx','swc_key_event_buffer','swc_m20_v3_display'):
            self.assertNotIn(forbidden,top)
        gpio=(base/'swc_m20_v31_gpio.sv').read_text()
        self.assertIn('~{KEY6,KEY5,KEY1,KEY3,KEY0,KEY2}',gpio)
        self.assertIn('assign {oled_cs_n,oled_dc,oled_sck,oled_mosi}=gpo',gpio)
        self.assertNotIn('swc_debounce',gpio)

    def test_pong_restart_redraws_stationary_paddles_and_plus_ball(self):
        r=Runner();r.boot();r.select('pong')
        # The two original paddle positions remain2 on restart. A real screen
        # clear must invalidate the software old-position cache even unchanged.
        for _ in range(2):
            for _ in range(4):r.visit('game_poll',0)
            r.cpu.keys=16;r.until('restart_game');r.step();r.until('game_poll')
            r.check_pixels('pong')
            for x,a in ((0,4),(15,5)):
                for y in range(r.cpu.ram[a],r.cpu.ram[a]+3):
                    self.assertEqual(r.oled.ram[y*128+x*8:y*128+x*8+8],[255]*8)
            x,y=r.cpu.ram[0],r.cpu.ram[1]
            self.assertEqual(r.oled.ram[y*128+x*8:y*128+x*8+8],[0,0,24,126,126,24,0,0])

    def test_snake_food_is_plus_in_decoded_software_spi(self):
        r=Runner();r.boot();r.select('snake')
        r.check_pixels('snake')
        x,y=r.cpu.ram[7:9]
        self.assertEqual(r.oled.ram[y*128+x*8:y*128+x*8+8],[0,0,24,126,126,24,0,0])
