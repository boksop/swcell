import hashlib,json,tempfile,unittest
from pathlib import Path
from m20.v21_build import generate,ROOT
from m20.v21_audit import audit,AuditError

class V21AuditTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name)
  self.d=self.base/'generated';self.net=generate(self.d)
  self.primitive=self.base/'swc_mux157.sv';self.primitive.write_bytes((ROOT/'rtl/m20/v21/swc_mux157.sv').read_bytes())
  self.sv=self.d/'m20v21_cpu_core.sv';self.j=self.d/'m20v21_cpu_core.netlist.json'
 def run_audit(self):return audit(self.sv,self.j,self.primitive)
 def save(self,text=None):
  if text is not None:self.sv.write_text(text)
  self.net['source_sha256']=hashlib.sha256(self.sv.read_bytes()).hexdigest();self.j.write_text(json.dumps(self.net))
 def test_deterministic_and_two_cones(self):
  other=self.base/'other';generate(other)
  self.assertEqual(self.sv.read_bytes(),(other/self.sv.name).read_bytes())
  self.assertEqual(self.j.read_bytes(),(other/self.j.name).read_bytes())
  a=self.run_audit();self.assertEqual((a['full_equivalent'],a['functional_equivalent'],a['ff_bits'],a['max_mux_depth']),(543,542,33,29))
 def test_pin_mismatch_rejected(self):
  self.net['nodes'][0]['i0']='0' if self.net['nodes'][0]['i0']!='0' else '1';self.save()
  with self.assertRaises(AuditError):self.run_audit()
 def test_forged_count_rejected(self):
  self.net['physical_mux_count']=300;self.save()
  with self.assertRaises(AuditError):self.run_audit()
 def test_hidden_logic_rejected_even_with_matching_hash(self):
  self.save(self.sv.read_text().replace('endmodule','wire sneaky; assign sneaky = rst & clk;\nendmodule'))
  with self.assertRaises(AuditError):self.run_audit()
 def test_hidden_ff_control_rejected(self):
  self.save(self.sv.read_text().replace('pc_reg <=','if(rst) pc_reg <='))
  with self.assertRaises(AuditError):self.run_audit()
 def test_cycle_rejected_even_when_pins_match_json(self):
  n=self.net['nodes'][0];old=n['s'];n['s']=n['id']
  self.save(self.sv.read_text().replace(f'.s({old})',f'.s({n["id"]})',1))
  with self.assertRaises(AuditError):self.run_audit()
 def test_output_multidriver_rejected(self):
  self.save(self.sv.read_text().replace('endmodule','assign ram_ce = rst;\nendmodule'))
  with self.assertRaises(AuditError):self.run_audit()

 def test_fake_cpu_input_port_rejected(self):
  self.net['inputs']['free_decode']=1
  self.save(self.sv.read_text().replace('input wire clk,','input wire free_decode,\n    input wire clk,'))
  with self.assertRaises(AuditError):self.run_audit()
 def test_reset_manifest_cannot_override_isa(self):
  self.net['registers'][0]['reset_value']=1;self.save()
  with self.assertRaises(AuditError):self.run_audit()
