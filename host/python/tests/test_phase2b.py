import hashlib
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from swcell_phase2b import windows,phase_points,frequency_summary,Runner,zero,verify_job,export,adjacent_transitions,main,fingerprint
from swcell_hs import FIELDS,LANE_FIELDS,parse_hs


def record(point,qerr=0,merr=0):
    hz,q,m,n,p,scan=point
    r={k:0 for k in (*FIELDS,*LANE_FIELDS)}
    r.update(type='PHASE_RESULT' if scan else 'FREQ_RESULT',module='M11',protocol_version=2,
             frequency_hz=hz,q_sample_phase=q,qm_sample_phase=m,requested_bits=n,pattern=p,
             total_bits=n,qm_total_bits=n,q_errors=qerr,qm_errors=merr,status='CAPTURE_ERRORS' if qerr or merr else 'PASS')
    if qerr:r.update(q_first_expected=0,q_first_actual=1,q_first_error_cycle=1)
    if merr:r.update(qm_first_expected=1,qm_first_actual=0,qm_first_error_cycle=2)
    return r

class Phase2BTests(unittest.TestCase):
    def test_resume_does_not_prefetch_a_finished_axis_point(self):
        point=(75000000,0,6,10000,5,1);calls=[]
        state=dict(schema_version=1,source_sha256=fingerprint(),status='INTERRUPTED',
                   config=dict(frequencies=[75000000],scan_bits=10000,minimum_window_bins=3,q_anchor=12,qm_anchor=6),
                   attempts=[dict(id='q_'+'_'.join(map(str,point)),point=list(point),stage='q',status='UNSUPPORTED',reason='SYNTHETIC_TEST')])
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'checkpoint.json').write_text(json.dumps(state))
            def build(p,args):
                calls.append(p);return root,dict(status='UNSUPPORTED',reason='SYNTHETIC_TEST')
            with patch('swcell_phase2b.build_point',side_effect=build):
                self.assertEqual(main(['--build-only','--resume','--jobs','2','--frequencies','75000000','--output',d]),0)
        self.assertNotIn(point,calls)
        self.assertEqual(len(calls),30)  # 31 unique images less the finished point
    def test_future_frequency_builds_do_not_compete_with_gated_long_stage(self):
        allowed=[75000000];active=[0];peak=[0];lock=threading.Lock()
        with tempfile.TemporaryDirectory() as d:
            def build(point,args):
                with lock:
                    self.assertEqual(point[0],allowed[0],'Future frequency started during previous long stage')
                    active[0]+=1;peak[0]=max(peak[0],active[0])
                time.sleep(.003)
                with lock:active[0]-=1
                return Path(d),dict(status='UNSUPPORTED',reason='SYNTHETIC_TEST')
            def frequency(runner,hz):
                for future in runner.futures.values():future.result()
                # Simulate the dependency-gated long stage after scan completion.
                time.sleep(.05)
                with lock:
                    self.assertEqual(active[0],0)
                    allowed[0]=100000000 if hz==75000000 else None
            with patch('swcell_phase2b.build_point',side_effect=build),patch.object(Runner,'frequency',frequency):
                self.assertEqual(main(['--build-only','--jobs','2','--frequencies','75000000,100000000','--output',str(Path(d)/'run')]),0)
            self.assertLessEqual(peak[0],2)
    def test_all_windows_and_epoch_boundaries(self):
        q=windows([0,1,2,5,6,7,14,15],'q')
        self.assertEqual([w['bins'] for w in q],[[0,1,2],[5,6,7],[14,15]])
        self.assertEqual(q[-1]['status'],'MARGINAL_WINDOW')
        self.assertEqual(windows([14,15,0,1,2],'qm')[0]['bins'],[14,15,0,1,2])
        self.assertEqual(len(windows([6,7,8,9],'qm')),2)
        self.assertEqual(windows([],'q'),[])
        self.assertEqual(windows([3],'q')[0]['status'],'MARGINAL_WINDOW')
    def test_full_independent_axes(self):
        points=phase_points(75000000,10000)
        self.assertEqual(len(points),32)
        self.assertEqual({p[1][1] for p in points[:16]},set(range(16)))
        self.assertEqual({p[1][2] for p in points[16:]},set(range(16)))
        self.assertTrue(all(p[1][2]==6 for p in points[:16]))
    def exercise_gate(self,fail_stage=None):
        state=dict(source_sha256='synthetic',status='RUNNING',attempts=[],config=dict(frequencies=[75000000],scan_bits=10000,q_anchor=12,qm_anchor=6,minimum_window_bins=3))
        calls=[]
        with tempfile.TemporaryDirectory() as d:
            runner=Runner(SimpleNamespace(build_only=False),Path(d),state)
            def measure(stage,point):
                calls.append((stage,point))
                qe=0 if point[1] in (10,11,12,13,14) else 5
                me=0 if point[2] in (3,4,5,6,7) else 5
                if stage not in ('q','qm'):qe=5 if stage==fail_stage else 0;me=0
                r=record(point,qe,me)
                state['attempts'].append(dict(id=str(len(calls)),stage=stage,point=list(point),status='MEASURED',result=r))
                return r
            runner.measure=measure;runner.frequency(75000000)
        return calls,state
    def test_gated_sequence(self):
        calls,state=self.exercise_gate()
        self.assertEqual([s for s,p in calls[:32]],['q']*16+['qm']*16)
        self.assertEqual([s for s,p in calls[32:]],['alignment','alignment','million','hundred_million'])
        self.assertEqual(calls[-1][1],(75000000,12,5,100000000,5,0))
        self.assertEqual(frequency_summary(75000000,state['attempts'],3)['status'],'PASS_1E8_ZERO_ERRORS')
    def test_failed_million_or_alignment_never_runs_1e8(self):
        for fail in ('million','alignment'):
            calls,_=self.exercise_gate(fail)
            self.assertNotIn('hundred_million',[s for s,p in calls])
    def test_failed_hundred_million_cannot_be_reported_pass_million_only(self):
        _,state=self.exercise_gate('hundred_million')
        self.assertEqual(frequency_summary(75000000,state['attempts'],3)['status'],'INCONCLUSIVE')
    def test_marginal_long_zero_is_not_promoted_to_reliable_window(self):
        _,state=self.exercise_gate()
        for j in state['attempts']:
            if j['stage']=='q' and j['point'][1] not in (12,13):j['result']=record(j['point'],5000,0)
        s=frequency_summary(75000000,state['attempts'],3)
        self.assertEqual(s['status'],'MARGINAL_WINDOW')
        self.assertEqual(s['observed_zero_error_1e8_pairs'][0]['q'],12)
    def test_q_no_window_still_completes_qm(self):
        state=dict(attempts=[],config=dict(scan_bits=10000,q_anchor=12,qm_anchor=6,minimum_window_bins=3))
        runner=Runner(SimpleNamespace(build_only=False),Path('/unused'),state)
        calls=[]
        def measure(stage,point):
            calls.append(stage)
            state['attempts'].append(dict(id=str(len(calls)),stage=stage,point=list(point),status='MEASURED',result=record(point,5000,0)))
        runner.measure=measure;runner.frequency(75000000)
        self.assertEqual(calls,['q']*16+['qm']*16)
        self.assertEqual(frequency_summary(75000000,state['attempts'],3)['status'],'NO_VALID_CAPTURE_WINDOW')
    def test_transition_diagnostic_with_independent_list(self):
        bits=[];state=0x13579bdf
        for _ in range(400):
            bits.append((state>>30)&1)
            state=((state<<1)&0x7fffffff)|(((state>>30)^(state>>27))&1)
        start=0x13579bdf
        for _ in range(50):start=((start<<1)&0x7fffffff)|(((start>>30)^(start>>27))&1)
        self.assertEqual(adjacent_transitions(start,200),sum(bits[i]!=bits[i-1] for i in range(50,250)))
    def test_other_lane_errors_do_not_hide_zero_window(self):
        jobs=[]
        for stage,point in phase_points(100000000,10000):
            jobs.append(dict(id=str(len(jobs)),stage=stage,point=point,status='MEASURED',result=record(point,0 if stage=='q' else 5000,0 if stage=='qm' else 5000)))
        result=frequency_summary(100000000,jobs,3)
        self.assertTrue(all(result['complete'].values()))
        self.assertEqual(result['windows']['q'][0]['width_bins'],16)
        self.assertEqual(result['windows']['qm'][0]['width_bins'],16)
    def test_missing_is_not_no_window(self):
        self.assertEqual(frequency_summary(125000000,[],3)['status'],'INCONCLUSIVE')
    def test_partial_scan_single_good_bin_is_not_final_marginal(self):
        jobs=[]
        for stage,point in phase_points(75000000,10000):
            if stage=='qm' and point[2]>1:continue
            jobs.append(dict(id=str(len(jobs)),stage=stage,point=list(point),status='MEASURED',
                             result=record(point,0,0 if point[2]==1 else 5000)))
        self.assertEqual(frequency_summary(75000000,jobs,3)['status'],'INCONCLUSIVE')
    def test_unsupported_phase_is_a_reported_gap_not_a_dut_error(self):
        jobs=[]
        for stage,point in phase_points(125000000,10000):
            unsupported=(stage=='q' and point[1]==1)
            jobs.append(dict(id=str(len(jobs)),stage=stage,point=list(point),status='UNSUPPORTED' if unsupported else 'MEASURED',reason='FPGA_TIMING',result=record(point,5000,5000)))
        s=frequency_summary(125000000,jobs,3)
        self.assertTrue(s['complete']['q'])
        self.assertFalse(s['measured_complete']['q'])
        self.assertEqual(s['unsupported_phases']['q'][0]['phase_index'],1)
        self.assertEqual(s['status'],'FPGA_TIMING_FAILURE')
    def test_independent_snapshot_protocol_backward_compatible(self):
        r=record((75000000,4,12,10000,5,1),100,500)
        self.assertEqual(parse_hs(r.copy())['qm_first_actual'],0)
        legacy={k:v for k,v in r.items() if k not in LANE_FIELDS}
        self.assertNotIn('q_first_expected',parse_hs(legacy))
        r['q_first_actual']=0
        with self.assertRaises(ValueError):parse_hs(r)
    def test_resume_raw_integrity_and_offline(self):
        point=(75000000,12,6,10000,5,1);r=record(point)
        records=[dict(r,type='SWEEP_START',status='RUNNING'),r,dict(r,type='SWEEP_COMPLETE')]
        data=('\n'.join(json.dumps(x) for x in records)+'\n').encode()
        with tempfile.TemporaryDirectory() as d:
            directory=Path(d);(directory/'raw.jsonl').write_bytes(data)
            job=dict(id='q_'+'_'.join(map(str,point)),stage='q',point=list(point),status='MEASURED',result=r,raw_file='raw.jsonl',raw_sha256=hashlib.sha256(data).hexdigest(),timing=dict(internal_timing_pass=True),build_dir=d,bitstream_sha256='synthetic')
            verify_job(job,directory)
            state=dict(attempts=[job],status='INTERRUPTED',source_sha256='synthetic',config=dict(frequencies=[75000000],minimum_window_bins=3))
            summary=export(directory,state,plots=True)
            self.assertEqual(summary['frequencies'][0]['status'],'INCONCLUSIVE')
            for name in ('phase_scan.csv','long_run.csv','summary.json','q_phase_scan.png','qm_phase_scan.png','frequency_summary.png','report.md'):self.assertTrue((directory/name).exists())
            runner=Runner(SimpleNamespace(),directory,state)
            with patch('swcell_phase2b.build_point',side_effect=AssertionError('must reuse verified point')):
                self.assertEqual(runner.measure('q',point),r)
            (directory/'raw.jsonl').write_bytes(data+b'bad\n')
            with self.assertRaises(ValueError):verify_job(job,directory)

if __name__=='__main__':unittest.main()
