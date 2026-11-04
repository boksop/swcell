import unittest
from m20.ff16_review import boundaries,config,load,ROOT,apply_loss

class FF16ReviewTests(unittest.TestCase):
    def test_preserved_measurements_match_recomputed_boundaries(self):
        import csv
        with (ROOT/'docs/m20/ff16_resources/timing_results.csv').open() as f:
            rows=list(csv.DictReader(f))
        for row in rows:
            if row['case']=='runt_high':continue
            b=boundaries(config(row['case'],int(row['tap'])))
            self.assertAlmostEqual(b['d1'],float(row['d1_ns']),places=3)
            self.assertAlmostEqual(b['d2'],float(row['d2_ns']),places=3)

    def test_global_extrema_equal_all_1089_signed_pairs(self):
        b=boundaries(config('mixed_stage',4));a=b['leaves']
        self.assertAlmostEqual(b['d1'],min(s['s_open']-m['m_close'] for m in a for s in a))
        self.assertAlmostEqual(b['d2'],min(m['m_open']-s['s_close'] for m in a for s in a))
        self.assertLess(b['d1'],0)
        self.assertGreater(min(v['s_open']-v['m_close'] for v in a),0)

    def test_independent_physical_component_spans_not_single_skew(self):
        cfg=config('independent_cross',16);apply_loss(cfg,chip=.5,branch=.2,pcb=1.,latch=4.)
        b=boundaries(cfg)
        self.assertAlmostEqual(b['d1'],b['root_d1']-5.7)
        self.assertAlmostEqual(b['d2'],b['root_d2']-5.7)
        cfg['leaves'][0]['so']+=.3
        self.assertNotAlmostEqual(boundaries(cfg)['d1'],boundaries(cfg)['d2'])

    def test_unknown_minimum_and_same_package_skew_are_distinct(self):
        devices=load(ROOT/'config/m20/ff16_buffer_sources.json')['devices']
        self.assertIsNone(devices[0]['tpd_min_ns'])
        for d in devices[1:4]:self.assertIsNone(d['part_to_part_skew_max_ns'])
        ti=devices[4]
        self.assertNotEqual(ti['output_skew_max_ns'],ti['tpd_max_ns']-ti['tpd_min_ns'])
