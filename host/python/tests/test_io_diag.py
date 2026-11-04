import copy
import json
from pathlib import Path
import re
import tempfile
import unittest
from io_diag import parse_record, StateCollector

ROOT = Path(__file__).resolve().parents[3]


def packet(**changes):
    row = dict(type='IO_STATE', build='OLEDKEYS01', keys='000', seen='000', events='00000000',
               presses=['00000000']*9, frame='00000001', mode='8', patterns='FF', up='00000001', oled=1, rx=0, merged='00000000')
    row.update(changes)
    return row


class IODiagnosticTests(unittest.TestCase):
    def test_real_snapshot_hex_fields_and_counter_width(self):
        record = parse_record(json.dumps(packet(keys='101', seen='1FF', events='FFFFFFFF', presses=['00000001']*9)))
        self.assertEqual(record['keys'], 257)
        self.assertEqual(record['events'], (1 << 32)-1)
        self.assertEqual(parse_record(json.dumps(packet(build='OLEDKEYS02')))['build'], 'OLEDKEYS02')
        self.assertEqual(parse_record(json.dumps(packet(build='OLEDKEYS03')))['build'], 'OLEDKEYS03')
        self.assertEqual(parse_record(json.dumps(packet(build='OLEDKEYS04')))['build'], 'OLEDKEYS04')
        for changes in [dict(keys='200'), dict(events='100000000'), dict(keys='001'), dict(presses=['00']*9), dict(oled=True), dict(build='OLD_IMAGE')]:
            with self.assertRaises(ValueError):
                parse_record(json.dumps(packet(**changes)))

    def test_input_coverage_is_not_visual_pass_and_reboot_clears_coverage(self):
        c = StateCollector()
        c.add(parse_record(json.dumps(packet(seen='1FF', presses=['00000001']*9))))
        c.add(parse_record(json.dumps(packet(keys='1FF', seen='1FF', presses=['00000001']*9, frame='00000002'))))
        self.assertTrue(c.summary()['all_levels_observed_by_host'])
        self.assertEqual(c.summary()['oled_visual_verification'], 'NOT_CONFIRMED')
        c.add(parse_record(json.dumps(packet(frame='00000000', up='00000000'))))
        self.assertEqual(c.resets, 1)
        self.assertFalse(c.summary()['all_inputs_seen_by_fpga'])
        with tempfile.TemporaryDirectory() as d:
            c.save(Path(d))
            self.assertTrue((Path(d)/'states.csv').is_file())

    def test_exact_user_pin_map_and_generated_xdc_no_cpu_dependency(self):
        manifest = json.loads((ROOT/'fpga/boards/swcell_k325t/oled_keys.json').read_text())
        pins = {v['port']: v['package_pin'] for v in manifest['pins']}
        expected = dict(OLED_RST_N='Y28', OLED_DC='M30', OLED_SCK='M29', OLED_MOSI='N24', OLED_CS_N='P22', RST_N='N27')
        expected.update({f'KEY{i}': p for i, p in enumerate('AK28 AF26 AE26 AG28 AF27 N19 M19 M27'.split())})
        expected.update({f'LED{i}': p for i, p in enumerate('AD27 AD28 AE29 AD29 AB28 AA27 Y30 Y29'.split())})
        self.assertTrue(expected.items() <= pins.items())
        self.assertEqual(len(set(pins.values())), len(pins))
        xdc = (ROOT/'fpga/projects/diagnostics/oled_keys/constraints/io.xdc').read_text()
        found = {port: pin for pin, port in re.findall(r'set_property PACKAGE_PIN (\w+) \[get_ports (\w+)\]', xdc)}
        self.assertEqual(pins, found)
        project = json.loads((ROOT/'fpga/projects/diagnostics/oled_keys/project.json').read_text())
        self.assertFalse(any('m20' in x or 'm11' in x for x in project['source_globs']))

    def test_font_source_matches_rtl_and_has_five_columns(self):
        font = json.loads((ROOT/'fpga/projects/diagnostics/oled_keys/font.json').read_text())['glyphs']
        rtl = (ROOT/'fpga/projects/diagnostics/oled_keys/rtl/swc_oled_font_pkg.sv').read_text()
        for char, columns in font.items():
            self.assertEqual(len(columns), 10)
            self.assertIn(f"8'h{ord(char):02x}:bits=40'h{columns}", rtl)
