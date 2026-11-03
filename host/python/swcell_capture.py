#!/usr/bin/env python3
"""Receive SwCell JSONL; preserve wire bytes and write validated results to CSV."""
from __future__ import annotations
import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import re
import sys
from contextlib import ExitStack

MAX_LINE_BYTES = 8192
CSV_FIELDS = ["module", "test", "total_checks", "error_checks", "q_errors", "qm_errors", "status"]
COUNTERS = {
    "TEST_START": (),
    "TEST_RESULT": ("total_checks", "error_checks", "q_errors", "qm_errors"),
    "FIRST_ERROR": ("cycle", "check", "inputs", "actual", "expected", "mask"),
    "TEST_COMPLETE": ("tests", "failed_tests"),
}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError(f"non-JSON numeric constant: {value}")


def parse_record(line: bytes | str) -> dict:
    """Validate one protocol record, converting numeric fields to Python integers."""
    if isinstance(line, bytes):
        line = line.decode("ascii", errors="strict")
    obj = json.loads(line, object_pairs_hook=_unique_object, parse_constant=_invalid_constant)
    if not isinstance(obj, dict):
        raise ValueError("record must be a JSON object")
    if obj.get('protocol_version') == 2:
        from swcell_hs import parse_hs
        return parse_hs(obj)
    kind = obj.get("type")
    if not isinstance(kind, str) or kind not in COUNTERS:
        raise ValueError(f"unknown record type: {kind!r}")
    if obj.get("module") != "M11":
        raise ValueError("unsupported module (expected M11)")
    if kind != "TEST_COMPLETE":
        if not isinstance(obj.get("test"), str) or not re.fullmatch(r"L0[1-8]|F0[1-9]", obj["test"]):
            raise ValueError("invalid M11 test name")
    for field in COUNTERS[kind]:
        value = obj.get(field)
        if isinstance(value, str) and re.fullmatch(r"0x[0-9a-fA-F]{1,16}", value):
            value = int(value, 16)
        if type(value) is not int or not 0 <= value <= 0xFFFFFFFFFFFFFFFF:
            raise ValueError(f"invalid unsigned 64-bit field: {field}")
        obj[field] = value
    if kind in ("TEST_RESULT", "TEST_COMPLETE") and obj.get("status") not in ("PASS", "FAIL"):
        raise ValueError("invalid status")
    if kind == "TEST_RESULT":
        n, err, q, qm = (obj[k] for k in COUNTERS[kind])
        if not max(q, qm) <= err <= min(n, q + qm):
            raise ValueError("inconsistent error counters")
        if (obj["status"] == "PASS") != (err == 0):
            raise ValueError("status disagrees with error count")
    if kind == "FIRST_ERROR":
        if obj["inputs"] > 15 or max(obj[k] for k in ("actual", "expected", "mask")) > 7:
            raise ValueError("snapshot bit vector outside defined width")
        if obj["check"] == 0 or not ((obj["actual"] ^ obj["expected"]) & obj["mask"]):
            raise ValueError("FIRST_ERROR does not describe a mismatch")
    if kind == "TEST_COMPLETE":
        if obj["failed_tests"] > obj["tests"] or (obj["status"] == "PASS") != (obj["failed_tests"] == 0):
            raise ValueError("inconsistent suite summary")
    return obj


class CaptureWriter:
    def __init__(self, directory: Path):
        self.directory = directory
        self._stack = ExitStack()
        self.records = self.invalid_lines = self.result_count = 0
        self.failed = self.complete_seen = False
        self._pending = bytearray()
        self._discard = False
        self.hs = None
        directory.mkdir(parents=True, exist_ok=False)
        try:
            self.raw = self._stack.enter_context((directory / "raw.jsonl").open("wb"))
            self.csv_file = self._stack.enter_context((directory / "results.csv").open("w", newline="", encoding="utf-8"))
            self.csv = csv.DictWriter(self.csv_file, fieldnames=CSV_FIELDS)
            self.csv.writeheader()
        except BaseException:
            self._stack.close()
            raise

    def _warn(self, message):
        self.invalid_lines += 1
        print(f"WARNING: {message}", file=sys.stderr, flush=True)

    def _line(self, line):
        try:
            record = parse_record(line)
        except (ValueError, UnicodeError, TypeError) as exc:
            self._warn(f"invalid JSONL record: {exc}; prefix={line[:100]!r}")
            return
        self.records += 1
        kind = record["type"]
        if record.get('protocol_version') == 2:
            from swcell_hs import HighSpeedAnalysis
            if self.hs is None:
                self.hs = HighSpeedAnalysis()
            self.hs.add(record)
            if kind in ('PHASE_RESULT', 'FREQ_RESULT'):
                self.result_count += 1
                self.failed |= record['status'] != 'PASS'
                print(f'{kind} {record["frequency_hz"]}Hz Qphase={record["q_sample_phase"]} '
                      f'QMphase={record["qm_sample_phase"]} {record["status"]} '
                      f'Q={record["q_errors"]}/{record["total_bits"]} QM={record["qm_errors"]}/{record["qm_total_bits"]}', flush=True)
            elif kind == 'SWEEP_COMPLETE':
                self.complete_seen = True
                self.failed |= record['status'] != 'PASS'
            return
        if kind == "TEST_RESULT":
            self.csv.writerow({k: record[k] for k in CSV_FIELDS})
            self.csv_file.flush()
            self.result_count += 1
            self.failed |= record["status"] == "FAIL"
            print(f'{record["test"]}: {record["status"]} checks={record["total_checks"]} '
                  f'Q={record["q_errors"]} QM={record["qm_errors"]}', flush=True)
        elif kind == "TEST_START":
            print(f'START {record["test"]}', flush=True)
        elif kind == "FIRST_ERROR":
            print(f'FIRST_ERROR {record["test"]} cycle={record["cycle"]} '
                  f'actual={record["actual"]:03b} expected={record["expected"]:03b}', flush=True)
        else:
            self.complete_seen = True
            self.failed |= record["status"] == "FAIL"
            print(f'COMPLETE {record["status"]} tests={record["tests"]} failed={record["failed_tests"]}', flush=True)

    def feed(self, chunk: bytes):
        # Store EVERY byte, including damaged, oversized and incomplete records.
        self.raw.write(chunk)
        self.raw.flush()
        for byte in chunk:
            if self._discard:
                if byte == 10:
                    self._discard = False
                continue
            if byte == 10:
                self._line(bytes(self._pending))
                self._pending.clear()
            else:
                self._pending.append(byte)
                if len(self._pending) > MAX_LINE_BYTES:
                    self._warn("oversized line discarded from parser (raw bytes retained)")
                    self._pending.clear()
                    self._discard = True

    def close(self):
        try:
            if self.hs is not None:
                self.hs.save(self.directory)
            if self._pending:
                self._warn("incomplete final JSONL line (raw bytes retained)")
                self._pending.clear()
            summary = dict(records=self.records, result_count=self.result_count,
                           invalid_lines=self.invalid_lines, complete_seen=self.complete_seen,
                           failed=self.failed, closed_at=datetime.now().astimezone().isoformat())
            (self.directory / "capture_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        finally:
            self._stack.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--port", help="e.g. /dev/ttyUSB0")
    source.add_argument("--input", type=Path, help="replay a saved JSONL file without pyserial")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--output-root", type=Path, default=Path("results"))
    parser.add_argument("--stop-on-complete", action="store_true")
    args = parser.parse_args(argv)
    if args.baud <= 0:
        parser.error("--baud must be positive")
    timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S_%f%z")
    directory = args.output_root / f"m11_{timestamp}"
    capture = None
    try:
        with ExitStack() as stack:
            # Open input first, so unavailable ports don't leave empty captures.
            if args.input:
                stream = stack.enter_context(args.input.open("rb"))
            else:
                try:
                    import serial
                except ImportError:
                    print("Install dependency: python3 -m pip install -r host/python/requirements.txt", file=sys.stderr)
                    return 2
                stream = stack.enter_context(serial.Serial(args.port, args.baud, timeout=0.2))
            capture = stack.enter_context(CaptureWriter(directory))
            (directory / "metadata.json").write_text(json.dumps(dict(
                started_at=datetime.now().astimezone().isoformat(), port=args.port,
                baud=args.baud, input=str(args.input) if args.input else None), indent=2) + "\n", encoding="utf-8")
            print(f"Saving to {directory}", flush=True)
            while True:
                chunk = stream.read(4096 if args.input else max(1, min(stream.in_waiting, 4096)))
                if chunk:
                    capture.feed(chunk)
                elif args.input:
                    break
                if args.stop_on_complete and capture.complete_seen:
                    break
        if capture.invalid_lines or (args.input and not capture.complete_seen):
            return 2
        return 1 if capture.failed else 0
    except KeyboardInterrupt:
        print("Capture stopped; files closed safely.", file=sys.stderr)
        return 130
    except (OSError, ValueError) as exc:
        print(f"Capture error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
