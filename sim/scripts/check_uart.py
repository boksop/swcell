#!/usr/bin/env python3
"""Independently validate every serial record from tb_m11 against the test plan."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "host/python"))
from swcell_capture import parse_record


def require(condition, message="UART semantic check failed"):
    if not condition:
        raise AssertionError(message)


def verify(path, fault):
    raw = Path(path).read_bytes()
    require(raw.endswith(b"\n"), "truncated UART stream")
    records = [parse_record(line) for line in raw.splitlines()]
    names = [f"L{i:02d}" for i in range(1, 9)] + [f"F{i:02d}" for i in range(1, 10)]
    bad_name = {0: None, 1: "L07", 2: "F08", 3: "F03"}[fault]
    counts = [1]*5 + [8, 8, 64] + [24]*5 + [192, 8, 8, 9]
    cursor = 0
    for name, count in zip(names, counts):
        start = records[cursor];cursor += 1
        require(start["type"] == "TEST_START" and start["test"] == name)
        bad = name == bad_name
        if bad:
            error = records[cursor];cursor += 1
            require(error["type"] == "FIRST_ERROR" and error["test"] == name)
            require(error["cycle"] > 0 and error["check"] == 1)
            require(error["mask"] == (1 if fault == 1 else 6))
            expected_mismatch = {1: 1, 2: 4, 3: 6}[fault]
            require((error["actual"] ^ error["expected"]) & error["mask"] == expected_mismatch)
        result = records[cursor];cursor += 1
        require(result["type"] == "TEST_RESULT" and result["test"] == name)
        require(result["total_checks"] == count)
        require(result["error_checks"] == (count if bad else 0))
        require(result["q_errors"] == (count if bad and fault != 2 else 0))
        require(result["qm_errors"] == (count if bad and fault != 1 else 0))
        require(result["status"] == ("FAIL" if bad else "PASS"))
    complete = records[cursor];cursor += 1
    require(cursor == len(records), "extra records")
    require(complete["type"] == "TEST_COMPLETE")
    require(complete["tests"] == 17 and complete["failed_tests"] == bool(fault))
    require(complete["status"] == ("FAIL" if fault else "PASS"))
    print(f"UART_PARSE_PASS fault={fault} records={len(records)} checks={sum(counts)}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("path", type=Path)
    p.add_argument("--fault", type=int, choices=range(4), required=True)
    a = p.parse_args()
    verify(a.path, a.fault)
