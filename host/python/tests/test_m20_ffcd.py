import tempfile,unittest
from pathlib import Path
from m20.ffcd_build import generate,ROOT
from m20.ffcd_audit import audit
from m20.ffcd_verify import checked

class FeedforwardSystemTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.p=Path(self.t.name)
  generate(self.p/'rtl',self.p/'sim');self.core=self.p/'rtl/m20ffcd_cpu_core.sv'
 def test_exact_563_and_deterministic_regeneration(self):
  a=audit(self.core);self.assertEqual((a['cpu_total'],a['generator_mux'],a['total_excluding_buffers'],a['native_ff_in_cpu_latch_branch']),(543,20,563,0))
  generate(self.p/'repeat',self.p/'repeat_sim')
  self.assertEqual(self.core.read_bytes(),(self.p/'repeat/m20ffcd_cpu_core.sv').read_bytes())
 def test_renamed_combinational_pin_rejected(self):
  self.core.write_text(self.core.read_text().replace('.i0(','.i1(',1))
  with self.assertRaises(AssertionError):audit(self.core)
 def test_wrong_state_mapping_rejected(self):
  self.core.write_text(self.core.read_text().replace('.q(state_q[0])','.q(state_q[1])',1))
  with self.assertRaises(AssertionError):audit(self.core)
 def test_hidden_native_state_rejected(self):
  self.core.write_text(self.core.read_text().replace('end else begin:g_bad','always_ff @(posedge clk) pc_reg<=0;end else begin:g_bad'))
  with self.assertRaises(AssertionError):audit(self.core)
 def test_cannot_overwrite_frozen_or_old_evidence(self):
  with self.assertRaises(AssertionError):checked(ROOT/'rtl/m20/v23',True)
  base=ROOT/'build/m20_300/v24_ffcd';base.mkdir(parents=True,exist_ok=True)
  with tempfile.TemporaryDirectory(prefix='fresh_guard_',dir=base) as existing:
   with self.assertRaises(AssertionError):checked(existing,True)
