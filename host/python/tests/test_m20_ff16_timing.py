import json,tempfile,unittest
from pathlib import Path
from m20.ff16_timing import config,prepare,summarize,input_hashes,checked,ROOT,TAPS
class FF16TimingTests(unittest.TestCase):
 def test_reconvergent_fast_close_uses_earlier_data_route(self):
  # At TAP4 Cd can close OR before its slow SELECT; old naive formula gave -8.
  v=config('fast_chain_sensitivity',4)
  self.assertEqual((v['predicted_full_pulse_d1_ns'],v['predicted_full_pulse_d2_ns']),(-7.,-7.))
 def test_global_overlap_can_exist_without_ownbit_overlap(self):
  v=config('independent_cross',4)
  self.assertEqual((v['predicted_full_pulse_d1_ns'],v['predicted_full_pulse_d2_ns']),(-2.,-2.))
  self.assertGreater(v['own_d1_min_ns'],0);self.assertGreater(v['own_d2_min_ns'],0)
 def test_unknown_minimum_not_reclassified_as_invalid_input(self):
  for tap in TAPS:
   v=config('fast_chain_sensitivity',tap)
   self.assertEqual(v['role'],'unqualified_minimum_sensitivity')
   self.assertLess(v['predicted_full_pulse_d1_ns'],0)
 def test_six_branches_and_loads_preserve_all33(self):
  for tap in TAPS:
   v=config('probe_load',tap)
   self.assertEqual([len(b['leaf_indices']) for b in v['buffer_branches']],[6,6,6,5,5,5])
   self.assertEqual(v['loads']['selected_tap_direct_mux_inputs'],2+(tap<16))
   self.assertEqual(len(v['gates']),20);self.assertEqual(len(v['leaves']),33)
 def test_actual_input_mutation_is_rejected_before_results(self):
  base=ROOT/'build/m20_300/v24_ff16';base.mkdir(parents=True,exist_ok=True)
  with tempfile.TemporaryDirectory(prefix='python_input_check_',dir=base) as t:
   d=Path(t)/'run';prepare(d)
   p=d/'tap4/nominal.cfg';p.write_text(p.read_text()+'\n')
   with self.assertRaisesRegex(ValueError,'input/config files changed'):summarize(d)
 def test_old_evidence_and_frozen_path_cannot_be_used_as_fresh_output(self):
  with self.assertRaises(ValueError):checked(ROOT/'rtl/m20/v23',True)
  with self.assertRaises(ValueError):checked(ROOT/'build/m20_300/v24_ff16/small_r4',True)
