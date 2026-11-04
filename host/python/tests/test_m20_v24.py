import unittest,tempfile,hashlib,json
from pathlib import Path
from m20.v24_build import generate,NAMES,ROOT
from m20.v24_audit import audit
from m20.v24_model import transition
class V24Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.d=Path(self.tmp.name)/'g';self.meta,self.c=generate(self.d)
 def test_reproducible_and_count(self):
  other=self.d.parent/'g2';generate(other)
  for p in self.d.iterdir():self.assertEqual(p.read_bytes(),(other/p.name).read_bytes())
  a=audit(self.d);self.assertEqual((a['comb_mux'],a['storage_bits'],a['storage_mux'],a['total_mux']),(88,13,26,116))
 def test_all_8192_states_all_requests_reset_against_independent_model(self):
  for state in range(1<<13):
   old={k:(state>>i)&1 for i,k in enumerate(NAMES)}
   for inp in range(8):
    inputs=dict(rst=inp&1,run_request=(inp>>1)&1,step_request=(inp>>2)&1)
    actual=self.c.eval(self.meta['d'],old|inputs)
    self.assertEqual(actual,transition(old,**inputs),(state,inp))
 def test_tamper_rejected(self):
  p=self.d/'swc157_phasegen_v24.sv';s=p.read_text().replace('.s(rst)','.s(run_request)',1);p.write_text(s)
  n=json.loads(p.with_suffix('.json').read_text());n['source_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();p.with_suffix('.json').write_text(json.dumps(n))
  with self.assertRaises(ValueError):audit(self.d)
 def test_extra_behavior_rejected(self):
  p=self.d/'swc157_phasegen_v24.sv';p.write_text(p.read_text().replace('endmodule','always @* $display("bad");\nendmodule'))
  n=json.loads(p.with_suffix('.json').read_text());n['source_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();p.with_suffix('.json').write_text(json.dumps(n))
  with self.assertRaises(ValueError):audit(self.d)
