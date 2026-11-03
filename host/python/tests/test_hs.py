import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from swcell_capture import parse_record, CaptureWriter
from swcell_hs import FIELDS,HighSpeedAnalysis,window_center

def point(hz=25000000,phase=4,n=4096,q=0,m=0,kind='PHASE_RESULT',status=None):
    r={k:0 for k in FIELDS}
    r.update(type=kind,protocol_version=2,module='M11',device='74LVC1G157',test='PRBS_STABILITY',
      frequency_hz=hz,d_phase=4,q_sample_phase=phase,qm_sample_phase=phase,
      pattern=5,requested_bits=n,total_bits=n,qm_total_bits=n,q_errors=q,qm_errors=m,
      status=status or ('CAPTURE_ERRORS' if q or m else 'PASS'),
      voltage_v=None,temperature_c=None,pcb_delay_ns=None)
    return r

class HighSpeedTests(unittest.TestCase):
    def test_circular_window_and_margin(self):
        w=window_center([14,15,0,1,2])
        self.assertEqual(w['center'],0)
        self.assertEqual(w['width_bins'],5)
        self.assertIsNone(window_center([1,2,4,5]))
    def test_separate_lanes_and_failed_repetition(self):
        a=HighSpeedAnalysis()
        for phase in range(16):a.add(point(phase=phase,q=0 if 3<=phase<=9 else 17,m=0 if phase in [13,14,15,0,1] else 11))
        w=a.windows()['25000000']
        self.assertEqual(w['q']['center'],6);self.assertEqual(w['qm']['center'],15)
        a.add(point(phase=6,q=1))
        self.assertNotEqual(a.windows()['25000000']['q']['center'],6)
    def test_no_valid_window(self):
        a=HighSpeedAnalysis()
        for p in range(16):a.add(point(phase=p,q=1,m=1))
        self.assertEqual(a.windows()['25000000']['status'],'NO_VALID_CAPTURE_WINDOW')
    def test_all_unsupported_is_distinct_from_bad_capture_window(self):
        a=HighSpeedAnalysis()
        for p in range(16):a.add(point(phase=p,n=0,status='UNSUPPORTED'))
        self.assertEqual(a.windows()['25000000']['status'],'UNSUPPORTED')
    def test_window_classification_and_unavailable_points(self):
        a=HighSpeedAnalysis()
        for p in range(1,8):a.add(point(phase=p,q=0 if 3<=p<=5 else 1))
        a.add(point(phase=8,n=0,status='UNSUPPORTED'))
        w=a.windows()['25000000']['phase_classification']['q']
        self.assertEqual(w['3'],'SELECTED_VALID_WINDOW')
        self.assertEqual(w['2'],'EARLY_SIDE_CANDIDATE')
        self.assertEqual(w['6'],'LATE_SIDE_CANDIDATE')
        self.assertEqual(w['8'],'UNAVAILABLE');self.assertEqual(w['9'],'UNAVAILABLE')
    def test_highest_requires_window_for_window_validated_field(self):
        a=HighSpeedAnalysis();a.add(point(n=1000000,kind='FREQ_RESULT'))
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(a.save(Path(tmp),plots=False)['highest_window_validated_zero_error_frequency_hz'])
            for p in (3,4,5):a.add(point(phase=p))
            self.assertEqual(a.save(Path(tmp),plots=False)['highest_window_validated_zero_error_frequency_hz'],25000000)
    def test_unsigned_64_and_rejections(self):
        r=point(n=2**64-1)
        for k in FIELDS:r[k]=f'0x{r[k]:016x}'
        self.assertEqual(parse_record(json.dumps(r))['total_bits'],2**64-1)
        for mutate in [lambda x:x.update(total_bits=-1),lambda x:x.update(total_bits=True),
                       lambda x:x.update(q_errors=4097),lambda x:x.update(status='RUNNING_UNKNOWN'),
                       lambda x:x.update(voltage_v=3.3),lambda x:x.update(q_sample_phase=16)]:
            r=point();mutate(r)
            with self.assertRaises(ValueError):parse_record(json.dumps(r))
    def test_incomplete_or_false_pass_rejected(self):
        for r in [point(q=1,status='PASS'),point(status='CAPTURE_ERRORS'),point()]:
            if r['status']=='PASS' and r['q_errors']==0:r['total_bits']-=1
            with self.assertRaises(ValueError):parse_record(json.dumps(r))
    def test_highest_excludes_scan_short_and_unsupported(self):
        a=HighSpeedAnalysis()
        a.add(point(hz=25000000,n=1000000,kind='FREQ_RESULT'))
        a.add(point(hz=50000000,n=1000,kind='FREQ_RESULT'))
        a.add(point(hz=75000000,n=1000000))
        a.add(point(hz=200000000,n=0,kind='FREQ_RESULT',status='UNSUPPORTED'))
        with tempfile.TemporaryDirectory() as tmp:
            s=a.save(Path(tmp),plots=False)
            self.assertEqual(s['highest_tested_zero_error_frequency_hz'],25000000)
            self.assertIsNone(json.loads((Path(tmp)/'summary.json').read_text())['zero_error_prbs_points'][0].get('theoretical_ber'))
    def test_transport_failure_invalidates_previous_result(self):
        a=HighSpeedAnalysis();a.add(point(n=1000000,kind='FREQ_RESULT'))
        a.add(point(n=0,kind='FREQ_RESULT',status='TRANSPORT_ERROR'))
        with tempfile.TemporaryDirectory() as tmp:self.assertIsNone(a.save(Path(tmp),plots=False)['highest_tested_zero_error_frequency_hz'])
    def test_unselected_summary_does_not_reject_an_actual_phase_zero_point(self):
        a=HighSpeedAnalysis();a.add(point(phase=0,n=1000000,kind='FREQ_RESULT'))
        r=point(phase=0,n=0,kind='FREQ_RESULT',status='NO_VALID_CAPTURE_WINDOW')
        r.update(test='SCAN_SUMMARY',source='host',selection_valid=False);a.add(r)
        with tempfile.TemporaryDirectory() as tmp:self.assertEqual(a.save(Path(tmp),plots=False)['highest_tested_zero_error_frequency_hz'],25000000)
    def test_snapshot_validation(self):
        r=point(kind='ERROR_SNAPSHOT',q=1)
        r.update(first_error_lane=1,first_error_cycle=1,first_error_expected=1,first_error_actual=0)
        self.assertEqual(parse_record(json.dumps(r))['first_error_lane'],1)
        r['first_error_actual']=1
        with self.assertRaises(ValueError):parse_record(json.dumps(r))
    def test_v2_capture_fragmentation_and_cleanup(self):
        r=point();end=point(kind='SWEEP_COMPLETE')
        wire=(json.dumps(r)+'\n'+json.dumps(end)+'\n').encode()
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)/'capture'
            with CaptureWriter(directory) as capture:
                for i in range(0,len(wire),7):capture.feed(wire[i:i+7])
            self.assertEqual((directory/'raw.jsonl').read_bytes(),wire)
            self.assertTrue(capture.complete_seen)
            self.assertFalse(capture.failed)
            self.assertTrue((directory/'phase_sweep.csv').exists())
    def test_hundreds_of_points_saved_without_counter_rounding(self):
        a=HighSpeedAnalysis()
        for h in range(1,21):
            for phase in range(16):a.add(point(hz=h*1000000,phase=phase,n=100000000))
        with tempfile.TemporaryDirectory() as tmp:
            a.save(Path(tmp),plots=False)
            lines=(Path(tmp)/'phase_sweep.csv').read_text().splitlines()
            self.assertEqual(len(lines),321)
            self.assertIn('100000000',lines[-1])

if __name__=='__main__':unittest.main()
