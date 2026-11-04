import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import tempfile
import unittest
from m20_fpga import parse_record
from m20_fpga.capture import WIDTHS

ROOT=Path(__file__).resolve().parents[3]

class M20V3Tests(unittest.TestCase):
    def test_shuffled_snake_is_reproducible_and_original_rom_is_preserved(self):
        spec=importlib.util.spec_from_file_location('shuffled_generator',ROOT/'tools/m20/v3_snake_shuffled.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        original=ROOT/'software/m20_300/snake.asm';before=hashlib.sha256(original.read_bytes()).hexdigest()
        checked=ROOT/'software/m20_300/variants/snake_shuffled_v0_1'
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            out=Path(tmp)/'variant';module.generate(out)
            for name in ('snake_shuffled.asm','snake_shuffled.memh','food_table.json','manifest.json'):
                self.assertEqual((out/name).read_bytes(),(checked/name).read_bytes())
        table=json.loads((checked/'food_table.json').read_text())['positions']
        self.assertEqual({tuple(p) for p in table},{(x,y) for x in range(16) for y in range(8)})
        self.assertEqual(table[:2],[[10,3],[2,6]])
        self.assertEqual(len(table),128)
        self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(),before)

    def test_deterministic_binding_preserves_all_original_nodes(self):
        spec=importlib.util.spec_from_file_location('v3_generator',ROOT/'tools/m20/v3_generate.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            out=Path(tmp);module.generate(out)
            for name in ('m20v3_cpu_core.sv','binding_manifest.json','games.json','m20_v3_game_pkg.sv','pong.memh','snake.memh'):
                self.assertEqual((out/name).read_bytes(),(ROOT/'rtl/modules/m20/v3/generated'/name).read_bytes())
            binding=json.loads((out/'binding_manifest.json').read_text())
            self.assertEqual(len(binding['states']),33)
            source=(ROOT/binding['source']).read_bytes()
            self.assertEqual(hashlib.sha256(source).hexdigest(),binding['source_sha256'])
            old=re.findall(r'swc_mux157 (u_n\d+) \(([^;]+)\);',source.decode())
            new=re.findall(r'swc_v3_mux157 (u_n\d+) \(([^;]+)\);',(out/'m20v3_cpu_core.sv').read_text())
            self.assertEqual(old,new);self.assertEqual(len(new),477)

    def test_debug_packet_counter_width_ram_epoch_and_state_decode(self):
        row={k:'0'*n for k,n in WIDTHS.items()}
        row.update(type='M20_V3_STATE',build='M20V3F01',cycle_ticks='0032',micro='FFFFFFFFFFFFFFFF')
        debug=(0xabc<<69)|(0x56<<61)|(9<<57)|(1<<56)|(3<<51)|(2<<48)|(0xe000<<32)|(1<<2)
        row['debug']=f'{debug:024X}';row['ram']='A'+'0'*254+'5'
        result=parse_record(json.dumps(row))
        self.assertEqual((result['pc'],result['ar'],result['a'],result['z'],result['gpo'],result['ustate'],result['rom_word'],result['run']),
                         (0xabc,0x56,9,1,3,2,0xe000,1))
        self.assertEqual(result['micro'],2**64-1)
        self.assertEqual((result['ram_cells'][0],result['ram_cells'][255]),(5,10))
        buffered=row|dict(build='M20V3F04',debug=f'{debug|(8<<91)|(5<<81)|(1<<95):024X}')
        observed=parse_record(json.dumps(buffered))
        self.assertEqual((observed['queued_keys'],observed['input_overflows']),(8,5))
        for version in ('M20V3F05','M20V3F06'):
            remapped=parse_record(json.dumps(buffered|dict(build=version)))
            self.assertEqual((remapped['queued_keys'],remapped['input_overflows']),(8,5))
        with self.assertRaises(ValueError):parse_record(json.dumps(row|dict(debug=f'{debug|(9<<91):024X}')))
        for change in ({'ram':'Z'*256},{'cycle_ticks':'0001'},{'frame_ticks':'0000000000000001'},{'game':'2'},{'micro':'0'*17}):
            with self.assertRaises(ValueError):parse_record(json.dumps(row|change))

    def test_no_global_false_path_or_combinatorial_loop_waiver(self):
        text=(ROOT/'fpga/projects/m20/cpu_validation/scripts/build.tcl').read_text()
        self.assertNotIn('ALLOW_COMBINATORIAL_LOOPS',text)
        exceptions=[line.strip() for line in text.splitlines() if line.strip().startswith('set_false_path')]
        self.assertEqual(len(exceptions),2)
        self.assertTrue(all('get_ports' in line and '-to' in line for line in exceptions))
        top=(ROOT/'fpga/projects/m20/cpu_validation/rtl/swcell_m20_v3_top.sv').read_text()
        self.assertIn('{buttons[6],buttons[5],buttons[1],buttons[3],buttons[0],buttons[2]}',top)
