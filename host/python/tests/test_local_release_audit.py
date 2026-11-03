"""Local version checks must not depend on ignored evidence or mutate the index."""
import hashlib,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]

class LocalReleaseAuditTests(unittest.TestCase):
 def test_fingerprints_do_not_read_ignored_v1_manifest(self):
  from m20.v2_verify import fingerprints
  from m20.v21_verify import sources
  original=Path.read_text
  def guarded(path,*a,**kw):
   if path==ROOT/'build/m20_300/v1/inputs_manifest.json':raise AssertionError('ignored historical dependency')
   return original(path,*a,**kw)
  with patch.object(Path,'read_text',guarded):
   self.assertIn('software/m20_300/reference/v1_source_paths.json',fingerprints())
   self.assertIn('software/m20_300/reference/v1_source_paths.json',sources())
 def invoke(self,manifest,output):
  env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
  return subprocess.run([sys.executable,'-B',str(ROOT/'tools/git/local_release_audit.py'),'--root',str(ROOT),'--manifest',str(manifest),'--output',str(output)],env=env,text=True,capture_output=True)
 def test_bad_manifest_is_rejected_without_changing_sources(self):
  path=ROOT/'docs/m20/M20_SOURCE_MANIFEST.json';j=json.loads(path.read_text());j['files']['rtl/m20/v21/swc_mux157.sv']='0'*64
  before=hashlib.sha256((ROOT/'rtl/m20/v21/swc_mux157.sv').read_bytes()).hexdigest()
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'bad.json';p.write_text(json.dumps(j));out=Path(tmp)/'audit'
   r=self.invoke(p,out);self.assertNotEqual(r.returncode,0)
   report=json.loads((out/'release_audit.json').read_text());self.assertIn('SHA mismatch rtl/m20/v21/swc_mux157.sv',report['errors'])
  self.assertEqual(before,hashlib.sha256((ROOT/'rtl/m20/v21/swc_mux157.sv').read_bytes()).hexdigest())
 def test_audit_is_read_only_for_git_index(self):
  index=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','--git-path','index'],text=True).strip()
  index=Path(index) if Path(index).is_absolute() else ROOT/index
  before=hashlib.sha256(index.read_bytes()).hexdigest()
  with tempfile.TemporaryDirectory() as tmp:
   r=self.invoke(ROOT/'docs/m20/M20_SOURCE_MANIFEST.json',Path(tmp)/'audit')
   self.assertEqual(r.returncode,0,r.stdout+r.stderr)
  self.assertEqual(before,hashlib.sha256(index.read_bytes()).hexdigest())
