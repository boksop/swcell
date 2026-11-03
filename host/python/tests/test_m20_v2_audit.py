"""Independent counter negative tests; no fake RTL success files are produced."""
from contextlib import redirect_stdout
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from m20.v2_audit import ROOT, AuditError, audit_module, audit_primitive, run


class MuxAuditTests(unittest.TestCase):
    def setUp(self):
        self.original=ROOT/'rtl/m20/v2/generated/shared/m20v2_cpu_core.sv'
        self.source=self.original.read_text()
        self.net=json.loads(self.original.with_suffix('.netlist.json').read_text())

    def check_changed(self,text=None,manifest=None):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'core.sv';j=p.with_suffix('.json')
            text=self.source if text is None else text
            manifest=copy.deepcopy(self.net) if manifest is None else manifest
            manifest['source_sha256']=hashlib.sha256(text.encode()).hexdigest()
            p.write_text(text);j.write_text(json.dumps(manifest))
            return audit_module(p,j)

    def test_actual_six_modules_and_top_only_accounting(self):
        for variant in ('baseline','shared'):
            for module in ('m20v2_cpu_core','m20v2_decoder','m20v2_alu'):
                p=ROOT/f'rtl/m20/v2/generated/{variant}/{module}.sv'
                result=audit_module(p,p.with_suffix('.netlist.json'))
                self.assertEqual(result['physical_157_equivalent'],result['combinational_mux']+2*result['state_bits'])
                self.assertEqual(sum(g['combinational_mux'] for g in result['groups']),result['combinational_mux'])
                self.assertEqual(result['state_bits'],33 if module.endswith('cpu_core') else 0)

    def test_pin_count_and_shared_connection_claims_are_independently_rejected(self):
        net=copy.deepcopy(self.net);net['physical_mux_count']-=1
        with self.assertRaises(AuditError):self.check_changed(manifest=net)
        net=copy.deepcopy(self.net);net['nodes'][0]['i0']='1' if net['nodes'][0]['i0']!='1' else '0'
        with self.assertRaises(AuditError):self.check_changed(manifest=net)
        net=copy.deepcopy(self.net);net['shared_requests'][0]['id']='missing_gate'
        with self.assertRaises(AuditError):self.check_changed(manifest=net)

    def test_hidden_behavior_and_extra_functional_state_are_rejected(self):
        text=self.source.replace('endmodule','assign uncounted = rom_data[0] & rom_data[1];\nendmodule')
        with self.assertRaises(AuditError):self.check_changed(text=text)
        text=self.source.replace('endmodule','logic secret; always_ff @(posedge clk) begin secret <= 1\'b0; end\nendmodule')
        net=copy.deepcopy(self.net);net['ff_bits']+=1
        net['registers'].append(dict(name='secret',width=1,qbits=['secret'],dbits=['0'],reset_value=0,
             storage='unconditional_native_ff',physical_storage_mux_per_bit=2))
        with self.assertRaises(AuditError):self.check_changed(text=text,manifest=net)

    def test_combinational_loop_with_matching_sv_and_manifest_is_rejected(self):
        net=copy.deepcopy(self.net);node=net['nodes'][0]
        old=node['s'];node['s']=node['y']
        sv_old='.S('+("1'b"+old if old in ('0','1') else old)+')'
        text=self.source.replace(sv_old,f'.S({node["y"]})',1)
        with self.assertRaises(AuditError):self.check_changed(text=text,manifest=net)

    def test_unique_primitive_and_reproducible_csv_markdown_ledger(self):
        primitive=ROOT/'rtl/m20/v2/swc_mux157.sv'
        audit_primitive(primitive)
        with tempfile.TemporaryDirectory() as directory:
            bad=Path(directory)/'bad.sv';bad.write_text(primitive.read_text().replace('S ? I1 : I0','S ? I0 : I1'))
            with self.assertRaises(AuditError):audit_primitive(bad)
            with redirect_stdout(io.StringIO()):result=run(ROOT/'rtl/m20/v2/generated',Path(directory)/'report')
            self.assertEqual(result['variants']['shared']['physical_157_equivalent'],603)
            markdown=(Path(directory)/'report/mux_budget.md').read_text()
            self.assertIn('|控制/译码+uSTATE存储|76|219|+143|',markdown)


if __name__=='__main__':unittest.main()
