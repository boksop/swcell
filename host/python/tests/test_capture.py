import contextlib
import csv
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from swcell_capture import CaptureWriter, MAX_LINE_BYTES, main, parse_record

RESULT = dict(type="TEST_RESULT", module="M11", test="F03", total_checks="0x000000000000000a",
              error_checks="0x0000000000000002", q_errors="0x0000000000000002", qm_errors="0x0", status="FAIL")
COMPLETE = dict(type="TEST_COMPLETE", module="M11", tests="0x11", failed_tests="0x1", status="FAIL")


class CaptureTests(unittest.TestCase):
    def test_hex_and_64_bit_precision(self):
        r = dict(RESULT, total_checks="0xffffffffffffffff")
        self.assertEqual(parse_record(json.dumps(r))["total_checks"], 2**64-1)

    def test_malformed_and_schema(self):
        for text in ('{', '[]', '{"type": "unknown"}', '{"type":"TEST_START","type":"TEST_RESULT"}',
                     '{"type":"TEST_START","module":"M11","test":"L01","extra":NaN}',
                     json.dumps(dict(RESULT, total_checks=True)),
                     json.dumps(dict(RESULT, q_errors="0xffffffffffffffff")),
                     json.dumps(dict(RESULT, status="PASS")),
                     json.dumps(dict(COMPLETE, failed_tests="0x12"))):
            with self.subTest(text=text), self.assertRaises((ValueError, TypeError)):
                parse_record(text)

    def test_fragmented_input_raw_csv_and_cleanup(self):
        wire = b"garbage\n" + json.dumps(RESULT).encode() + b"\n" + json.dumps(COMPLETE).encode() + b"\ntruncated"
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            directory = Path(tmp)/"capture"
            with CaptureWriter(directory) as cap:
                for pos in range(0, len(wire), 7):
                    cap.feed(wire[pos:pos+7])
            self.assertTrue(cap.raw.closed)
            self.assertTrue(cap.csv_file.closed)
            self.assertEqual((directory/"raw.jsonl").read_bytes(), wire)
            with (directory/"results.csv").open() as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(rows[0]["total_checks"], "10")
            self.assertEqual(cap.invalid_lines, 2)
            self.assertTrue(cap.complete_seen)

    def test_oversized_line_recovers(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            with CaptureWriter(Path(tmp)/"capture") as cap:
                cap.feed(b"x"*(MAX_LINE_BYTES+10)+b"\n"+json.dumps(COMPLETE).encode()+b"\n")
            self.assertEqual(cap.invalid_lines, 1)
            self.assertTrue(cap.complete_seen)

    def test_cleanup_on_interrupt(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(KeyboardInterrupt):
                with CaptureWriter(Path(tmp)/"capture") as cap:
                    raise KeyboardInterrupt
            self.assertTrue(cap.raw.closed)
            self.assertTrue(cap.csv_file.closed)

    def test_replay_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            p = Path(tmp)/"wire.jsonl"
            p.write_text(json.dumps(RESULT)+"\n"+json.dumps(COMPLETE)+"\n")
            self.assertEqual(main(["--input",str(p),"--output-root",str(Path(tmp)/"out")]), 1)
            p.write_text("bad\n")
            self.assertEqual(main(["--input",str(p),"--output-root",str(Path(tmp)/"out")]), 2)


if __name__ == "__main__":
    unittest.main()
