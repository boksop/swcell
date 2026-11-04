import json
from pathlib import Path
import shutil
import tempfile
import unittest

from m20.ff16_structure import FOLDER,TAPS,StructureError,audit,evaluate,export


class FF16StructureTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.folder=self.base/'rtl'
        shutil.copytree(FOLDER,self.folder)

    def test_all_four_taps_keep20_physical_cells(self):
        for tap in TAPS:
            r=audit(self.folder,tap)
            self.assertEqual((r['physical_mux_count'],r['effective_delay_cells'],r['unselected_tail_cells']),(20,tap,16-tap))
            self.assertEqual(r['selected_tap_total_direct_mux_input_loads'],2+(tap<16))

    def test_invalid_tap_is_not_a_configuration(self):
        for tap in (0,1,5,20,4.0,True):
            with self.assertRaises(StructureError):audit(self.folder,tap)

    def test_truth_table_and_hold_are_distinct(self):
        self.assertEqual([evaluate(c,cd,0) for c,cd in ((0,0),(1,0),(1,1),(0,1))],[(False,False),(True,False),(True,True),(True,False)])
        for c in range(2):
            for cd in range(2):self.assertEqual(evaluate(c,cd,1),(True,False))

    def test_missing_unselected_tail_is_rejected(self):
        p=self.folder/'swc_ff16_phasegen.sv'
        p.write_text(p.read_text().replace(" swc_ff16_mux157 u_delay16(.s(1'b0),.i0(chain[15]),.i1(1'b0),.y(chain[16]));",''))
        with self.assertRaises(StructureError):audit(self.folder,4)

    def test_reversed_chain_or_feedback_is_rejected(self):
        p=self.folder/'swc_ff16_phasegen.sv'
        p.write_text(p.read_text().replace('.i0(chain[15]),.i1(1\'b0),.y(chain[16])','.i0(chain[16]),.i1(1\'b0),.y(chain[16])'))
        with self.assertRaises(StructureError):audit(self.folder)

    def test_hold_wrong_polarity_is_rejected(self):
        p=self.folder/'swc_ff16_phasegen.sv'
        p.write_text(p.read_text().replace(".i0(h_raw),.i1(1'b1)",".i0(h_raw),.i1(1'b0)"))
        with self.assertRaises(StructureError):audit(self.folder)

    def test_hidden_driver_is_rejected(self):
        p=self.folder/'swc_ff16_phasegen.sv'
        p.write_text(p.read_text().replace('endmodule','assign delayed_ref=clk_ref;\nendmodule'))
        with self.assertRaises(StructureError):audit(self.folder)

    def test_primitive_wrong_truth_is_rejected(self):
        p=self.folder/'swc_ff16_mux157.sv';p.write_text(p.read_text().replace('s?i1:i0','s?i0:i1'))
        with self.assertRaises(StructureError):audit(self.folder)

    def test_export_and_refuse_overwrite(self):
        out=self.base/'evidence';export(out)
        r=json.loads((out/'structure_audit.json').read_text());self.assertEqual(len(r['profiles']),4)
        import csv
        with (out/'tap_assembly.csv').open() as f:assembly=list(csv.DictReader(f))
        for tap in TAPS:self.assertEqual(sum(int(v['fitted']) for v in assembly if v['configuration']==f'TAP{tap}'),1)
        with self.assertRaises(StructureError):export(out)
