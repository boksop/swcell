#!/usr/bin/env python3
"""Verify a contiguous SPI MCS at address zero against its paired BIN image."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def check_images(mcs_path, bin_path, size_mib=32):
    if type(size_mib) is not int or size_mib<1:
        raise ValueError("size_mib must be positive")
    capacity = size_mib*1024*1024
    if Path(bin_path).stat().st_size>capacity:
        raise ValueError("BIN exceeds Flash capacity")
    payload = Path(bin_path).read_bytes()
    if not payload:
        raise ValueError("empty BIN image")
    base = offset = records = 0
    eof = False
    with Path(mcs_path).open(encoding="ascii") as stream:
        for line_number, line in enumerate(stream, 1):
            text = line.strip()
            if not text:
                continue
            if eof:
                raise ValueError(f"line {line_number}: data after EOF")
            if not text.startswith(":"):
                raise ValueError(f"line {line_number}: invalid Intel HEX prefix")
            try:
                record = bytes.fromhex(text[1:])
            except ValueError as exc:
                raise ValueError(f"line {line_number}: invalid hex") from exc
            if len(record)<5 or len(record)!=record[0]+5 or sum(record)&255:
                raise ValueError(f"line {line_number}: record length or checksum error")
            length, kind = record[0], record[3]
            address = int.from_bytes(record[1:3], "big")
            data = record[4:-1]
            if kind == 0:
                absolute = base+address
                end = absolute+length
                if absolute != offset or end>capacity:
                    raise ValueError(f"line {line_number}: noncontiguous/overlapping/out-of-range data")
                if end>len(payload) or payload[absolute:end]!=data:
                    raise ValueError(f"line {line_number}: MCS and BIN payload differ")
                offset = end
                records += 1
            elif kind == 1:
                if length or address:
                    raise ValueError("invalid EOF record")
                eof = True
            elif kind in (2, 4):
                if length!=2 or address:
                    raise ValueError("invalid extended-address record")
                base = int.from_bytes(data, "big") << (4 if kind==2 else 16)
            else:
                raise ValueError(f"unsupported Intel HEX record type {kind}")
    if not eof or offset!=len(payload):
        raise ValueError("missing EOF or incomplete MCS payload")
    return dict(size_mib=size_mib, start_address=0, image_bytes=offset,
                data_records=records,
                bin_sha256=hashlib.sha256(payload).hexdigest(),
                mcs_sha256=hashlib.sha256(Path(mcs_path).read_bytes()).hexdigest())


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mcs", type=Path, required=True)
    p.add_argument("--bin", type=Path, required=True)
    p.add_argument("--size-mib", type=int, default=32)
    p.add_argument("--report", type=Path)
    a = p.parse_args(argv)
    try:
        report = check_images(a.mcs, a.bin, a.size_mib)
        if a.report:
            a.report.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    except (OSError, ValueError, UnicodeError) as exc:
        print(f"FLASH_IMAGE_FAIL: {exc}", file=sys.stderr)
        return 2
    print(f'FLASH_IMAGE_CHECK_PASS bytes={report["image_bytes"]} sha256={report["bin_sha256"]}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
