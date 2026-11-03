"""Independent failures must remain failures even when an attacker refreshes SHA."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from m20.v23_build import generate,ROOT
from m20.v23_audit import audit,AuditError
from m20.v23_verify import checked,pressure

class V23Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.d=Path(self.tmp.name)/'generated';generate(self.d)
  self.s=self.d/'m20v23_cpu_core.sv';self.j=self.s.with_suffix('.netlist.json')
 def save(self,text):
  self.s.write_text(text);n=json.loads(self.j.read_text());n['source_sha256']=hashlib.sha256(self.s.read_bytes()).hexdigest();self.j.write_text(json.dumps(n))
 def test_deterministic(self):
  d=self.d.parent/'repeat';generate(d)
  for p in self.d.iterdir():self.assertEqual(p.read_bytes(),(d/p.name).read_bytes())
 def test_exact_543_and_no_native_latch_ff(self):
  a=audit(self.d);self.assertEqual((a['comb_mux'],a['state_bits'],a['two_phase_storage_mux'],a['full_equivalent'],a['two_phase_native_ff_bits']),(477,33,66,543,0))
 def test_changed_comb_pin_fails_even_refreshed_sha(self):
  self.save(self.s.read_text().replace('.i0(','.i1(',1))
  with self.assertRaises(AuditError):audit(self.d)
 def test_state_d_mapping_fails(self):
  self.save(self.s.read_text().replace('.q(state_q[0])','.q(state_q[1])',1))
  with self.assertRaises(AuditError):audit(self.d)
 def test_native_ff_smuggled_into_latch_fails(self):
  self.save(self.s.read_text().replace('end else begin:g_bad','always_ff @(posedge clk) pc_reg <= 0;\n end else begin:g_bad'))
  with self.assertRaises(AuditError):audit(self.d)
 def test_forged_count_fails(self):
  n=json.loads(self.j.read_text());n['total_full_interface']=300;self.j.write_text(json.dumps(n))
  with self.assertRaises(AuditError):audit(self.d)
 def test_extra_assign_in_binding_fails(self):
  self.save(self.s.read_text().replace('end else begin:g_bad','wire sneaky; assign sneaky = rst & clk; end else begin:g_bad'))
  with self.assertRaises(AuditError):audit(self.d)
 def test_frozen_output_rejected(self):
  with self.assertRaises(AssertionError):checked(ROOT/'rtl/m20/v21')
 def test_existing_evidence_rejected(self):
  with self.assertRaises(AssertionError):checked(ROOT/'build/m20_300/v23/session_20261103',True)
 def test_directed_scenarios_independently_interpreted(self):
  d=self.d.parent/'pressure';pressure(d);m=json.loads((d/'metadata.json').read_text())
  self.assertEqual(len(m['cases']),5)
  pc=json.loads((d/'pc0_pc1.expected.jsonl').read_text().splitlines()[0]);self.assertEqual((pc['pc'],pc['next_pc']),(1,2))
  ar=json.loads((d/'ar0_ar1.expected.jsonl').read_text().splitlines()[0]);self.assertEqual(ar['ar'],2)
  ac=json.loads((d/'a3_c.expected.jsonl').read_text().splitlines()[0]);self.assertEqual((ac['word'],ac['a'],ac['c']),(0x3001,7,1))
