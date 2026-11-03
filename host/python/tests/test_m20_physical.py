import json,unittest
from m20.physical import paths,shortest_pairs,ROOT

class PhysicalPathTests(unittest.TestCase):
 def toy(self):
  return dict(nodes=[dict(id='n0',s='ctrl',i0='a',i1='b',group='test')],
    inputs=dict(ctrl=1,a=1,b=1),registers=[dict(name='q',qbits=['q'],dbits=['n0'])],functional_outputs=dict(out=['n0']))
 def test_select_and_data_arcs_are_distinct(self):
  p=paths(self.toy(),dict(select_ns=dict(max=7),data_ns=dict(max=2)))
  self.assertEqual(p[0]['source'],'ctrl');self.assertEqual(p[0]['max_scenario_ns'],7)
  self.assertTrue(any(r['source']=='a' and r['max_scenario_ns']==2 for r in p))
 def test_minimum_topology_does_not_invent_hold_bound(self):
  n=self.toy();n['nodes'][0]['i0']='q';r=shortest_pairs(n)[0]
  self.assertEqual(r['mux_layers'],1);self.assertEqual(r['contamination_min_ns'],'');self.assertTrue(r['self_feedback'])
 def test_device_library_keeps_unprovided_dff_parameters_unknown(self):
  j=json.loads((ROOT/'config/m20/157_timing_models.json').read_text())
  for d in j['devices'].values():
   for key in ('setup_ns','hold_ns','clock_to_q_ns','tcd_guaranteed_min_ns'):self.assertIsNone(d[key])
   self.assertTrue(d['vcc_range_v'][0]<=3.3<=d['vcc_range_v'][1])
