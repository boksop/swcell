"""Exercise sweep orchestration without Vivado, serial hardware or synthetic evidence files."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import swcell_sweep
from swcell_hs import FIELDS,HighSpeedAnalysis

class SweepTests(unittest.TestCase):
    def execute(self,mode='normal',extra=()):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        root=Path(tmp.name);image=root/'image';image.mkdir()
        (image/'swcell_m11_hs_top.bit').write_bytes(b'UNIT TEST ONLY, NOT AN FPGA IMAGE')
        calls=[]
        def build(point,args):
            if mode=='unsupported':return image,dict(status='UNSUPPORTED',reason='FPGA_TIMING')
            if mode=='build_error':return image,dict(status='BUILD_ERROR',reason='UNIT_TEST_BUILD_ERROR')
            return image,dict(status='SUPPORTED',reason='UNIT_TEST_ONLY')
        def measure(point,out,args,raw,analysis):
            calls.append(point)
            if mode=='transport':raise RuntimeError('UNIT_TEST_UART_TIMEOUT')
            hz,q,m,n,pattern,scan=point
            record={key:0 for key in FIELDS}
            qe=n if scan and (mode=='no_window' or q not in (3,4,5)) else 0
            me=n if scan and (mode=='no_window' or m not in (5,6,7)) else 0
            record.update(type='PHASE_RESULT' if scan else 'FREQ_RESULT',protocol_version=2,
                module='M11',device='74LVC1G157',test='PRBS_STABILITY',
                frequency_hz=hz,d_phase=4,q_sample_phase=q,qm_sample_phase=m,
                pattern=pattern,requested_bits=n,total_bits=n,qm_total_bits=n,
                q_errors=qe,qm_errors=me,status='CAPTURE_ERRORS' if qe or me else 'PASS')
            analysis.add(record)
            raw.write((json.dumps(record)+'\n').encode())
            return record
        output=root/'run'
        with patch.object(swcell_sweep,'build_point',side_effect=build), \
             patch.object(swcell_sweep,'run_hardware',side_effect=measure), \
             patch.object(HighSpeedAnalysis,'plot'):
            code=swcell_sweep.main(['--frequencies','25000000','--output',str(output),*extra])
        return code,calls,output

    def test_select_independent_windows_then_important_long_patterns(self):
        code,calls,out=self.execute(extra=['--important-frequencies','25000000',
            '--important-bits','100000000','--patterns','0,1,2,3,5'])
        self.assertEqual(code,0)
        long=[p for p in calls if p[-1]==0]
        self.assertEqual(long,[(25000000,4,6,100000000,p,0) for p in (0,1,2,3,5)])
        summary=json.loads((out/'summary.json').read_text())
        self.assertEqual(summary['highest_window_validated_zero_error_frequency_hz'],25000000)
        self.assertEqual(summary['infrastructure_errors'],0)
    def test_unsupported_is_saved_separately_and_never_programmed(self):
        code,calls,out=self.execute('unsupported',extra=['--point','4','12'])
        self.assertEqual(code,0);self.assertFalse(calls)
        self.assertEqual((out/'raw.jsonl').read_bytes(),b'')
        host=json.loads((out/'host_events.jsonl').read_text())
        self.assertEqual(host['source'],'host');self.assertEqual(host['status'],'UNSUPPORTED')
        self.assertEqual((host['d_phase_mdeg'],host['q_phase_mdeg'],host['qm_phase_mdeg']),(90000,90000,270000))
        self.assertIsNone(json.loads((out/'summary.json').read_text())['highest_tested_zero_error_frequency_hz'])
    def test_build_error_has_infrastructure_exit_status(self):
        code,calls,out=self.execute('build_error',extra=['--point','4','12'])
        self.assertEqual(code,2);self.assertFalse(calls)
    def test_all_scanned_phases_unsupported_has_frequency_summary(self):
        code,calls,out=self.execute('unsupported')
        self.assertEqual(code,0);self.assertFalse(calls)
        summary=json.loads((out/'summary.json').read_text())
        self.assertEqual(summary['unsupported_points'],16)
        self.assertEqual(summary['all_scanned_phases_unsupported_frequencies_hz'],[25000000])
        self.assertIn('UNSUPPORTED',(out/'frequency_sweep.csv').read_text())
    def test_transport_error_excludes_success(self):
        code,calls,out=self.execute('transport',extra=['--point','4','12'])
        self.assertEqual(code,2)
        summary=json.loads((out/'summary.json').read_text())
        self.assertEqual(summary['infrastructure_errors'],1)
        self.assertIsNone(summary['highest_tested_zero_error_frequency_hz'])
    def test_no_window_prevents_long_run(self):
        code,calls,out=self.execute('no_window')
        self.assertEqual(code,1)
        self.assertTrue(all(p[-1]==1 for p in calls))
        self.assertEqual(json.loads((out/'summary.json').read_text())['measurement_failures'],1)
        records=[json.loads(line) for line in (out/'host_events.jsonl').read_text().splitlines()]
        self.assertEqual(records[-1]['status'],'NO_VALID_CAPTURE_WINDOW')
        self.assertFalse(records[-1]['selection_valid'])
        self.assertEqual(swcell_sweep.parse_record(json.dumps(records[-1]))['status'],'NO_VALID_CAPTURE_WINDOW')
        self.assertIn('NO_VALID_CAPTURE_WINDOW',(out/'frequency_sweep.csv').read_text())

class BuildCacheTests(unittest.TestCase):
    def setUp(self):
        from types import SimpleNamespace
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.args=SimpleNamespace(rebuild=False,vivado='TEST_ONLY',build_timeout=1)
        self.point=(25000000,4,12,1000000,5,0)
        self.source='a'*64
        self.builds=0;self.exit_code=0
    def process(self,command,**kwargs):
        from types import SimpleNamespace
        self.builds+=1;out=Path(command[-1])
        (out/'build_status.json').write_text(json.dumps(dict(status='SUPPORTED',reason='UNIT_TEST_ONLY')))
        (out/'swcell_m11_hs_top.bit').write_bytes(b'UNIT_TEST_VALIDATED_IMAGE')
        return SimpleNamespace(wait=lambda **kw:self.exit_code)
    def test_corrupted_cache_is_rebuilt(self):
        with patch.object(swcell_sweep,'ROOT',self.root),patch.object(swcell_sweep,'fingerprint',return_value=self.source),patch.object(swcell_sweep.subprocess,'Popen',side_effect=self.process):
            out,state=swcell_sweep.build_point(self.point,self.args)
            swcell_sweep.build_point(self.point,self.args)
            self.assertEqual(self.builds,1)
            (out/'swcell_m11_hs_top.bit').write_bytes(b'CORRUPTED')
            swcell_sweep.build_point(self.point,self.args)
            self.assertEqual(self.builds,2)
    def test_source_change_during_build_is_rejected(self):
        with patch.object(swcell_sweep,'ROOT',self.root),patch.object(swcell_sweep,'fingerprint',side_effect=[self.source,'b'*64]),patch.object(swcell_sweep.subprocess,'Popen',side_effect=self.process):
            out,state=swcell_sweep.build_point(self.point,self.args)
            self.assertEqual(state['status'],'BUILD_ERROR')
            self.assertEqual(state['reason'],'SOURCE_CHANGED_DURING_BUILD')
            self.assertEqual(json.loads((out/'build_status.json').read_text())['status'],'BUILD_ERROR')

    def test_failed_rebuild_cannot_reuse_success_marker(self):
        with patch.object(swcell_sweep,'ROOT',self.root),patch.object(swcell_sweep,'fingerprint',return_value=self.source),patch.object(swcell_sweep.subprocess,'Popen',side_effect=self.process):
            out,state=swcell_sweep.build_point(self.point,self.args)
            self.args.rebuild=True;self.exit_code=1
            out,state=swcell_sweep.build_point(self.point,self.args)
            self.assertEqual(state['status'],'BUILD_ERROR')
            self.assertEqual(json.loads((out/'build_status.json').read_text())['status'],'BUILD_ERROR')

if __name__=='__main__':unittest.main()
