"""Parser/negative-test fixtures, never evidence of actual RTL simulation."""
import csv
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from m20.rtl_regression import (FIELDS, DifferentialError, compare, make_case)


class RTLComparisonToolsTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.directory=Path(self.temporary.name)
        row,_=make_case(self.directory,'parser_fixture',[0x0007,0x8112,0xF100])
        self.metadata=dict(isa_id='test_fixture',timing_profile='test_fixture',suite='parser_fixture',cases=[row])
        (self.directory/'metadata.json').write_text(json.dumps(self.metadata))
        self.expected=[json.loads(line) for line in (self.directory/'parser_fixture.expected.jsonl').read_text().splitlines()]

    def synthetic_parser_input(self,events=None):
        # Only under TemporaryDirectory; never write an XSIM evidence directory.
        with (self.directory/'parser_fixture.rtl.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader()
            writer.writerows(self.expected if events is None else events)
        (self.directory/'parser_fixture.ram.final.memh').write_bytes(
            (self.directory/'parser_fixture.expected_ram.memh').read_bytes())

    def test_requires_actual_output_and_rejects_count_and_unknown_data(self):
        with self.assertRaises(FileNotFoundError):compare(self.directory)
        for events in (self.expected[:-1],self.expected+self.expected[-1:],
                       [dict(row,a='x') for row in self.expected]):
            self.synthetic_parser_input(events)
            with self.assertRaises(DifferentialError):compare(self.directory)

    def test_detects_each_observable_mismatch_and_preserves_failure_context(self):
        for field in FIELDS:
            index=1 if field in ('ram_addr','ram_data') else 0
            bad=[dict(row) for row in self.expected];bad[index][field]^=1
            self.synthetic_parser_input(bad)
            with self.subTest(field=field),self.assertRaises(DifferentialError):compare(self.directory)
            failure=json.loads((self.directory/'first_mismatch.json').read_text())
            self.assertEqual(failure['instruction_index'],index)
            self.assertIn('expected',failure);self.assertIn('actual',failure)

    def test_final_ram_is_checked_beyond_observed_transactions(self):
        self.synthetic_parser_input()
        with redirect_stdout(io.StringIO()):self.assertEqual(compare(self.directory),0)
        path=self.directory/'parser_fixture.ram.final.memh'
        original=path.read_text().splitlines();original[255]='0'
        path.write_text('\n'.join(original)+'\n')
        with self.assertRaises(DifferentialError):compare(self.directory)
        path.write_text('X\n')
        with self.assertRaises(DifferentialError):compare(self.directory)


if __name__=='__main__':unittest.main()
