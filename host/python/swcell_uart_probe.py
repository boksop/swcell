#!/usr/bin/env python3
"""Physical UART round-trip test; run only with the FPGA loopback diagnostic loaded."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True)
    parser.add_argument('--baud', type=int, default=115200)
    parser.add_argument('--output-root', type=Path, default=Path('results'))
    parser.add_argument('--pattern', help='Optional transmitted bytes as hexadecimal, e.g. 555500ff')
    parser.add_argument('--break-seconds', type=float, default=0,
                        help='Hold PC TX / FPGA RX low before data (0 to 10 seconds)')
    args = parser.parse_args()
    if not 0 <= args.break_seconds <= 10:
        parser.error('--break-seconds must be between 0 and 10')
    try:
        payload = bytes.fromhex(args.pattern) if args.pattern is not None else b'SWCELL_UART_LOOPBACK\r\n' + bytes(range(256))
    except ValueError:
        parser.error('--pattern must contain hexadecimal byte pairs')
    if not payload:
        parser.error('--pattern must contain at least one byte')
    import serial
    directory = args.output_root / ('uart_loopback_' + datetime.now().astimezone().strftime('%Y%m%d_%H%M%S_%f%z'))
    directory.mkdir(parents=True, exist_ok=False)
    received = bytearray()
    error = None
    try:
        with serial.Serial(args.port, args.baud, timeout=0.2, write_timeout=2, exclusive=True) as port:
            port.reset_input_buffer()
            if args.break_seconds:
                print(f'Holding FPGA RX low for {args.break_seconds:g} seconds', flush=True)
                try:
                    port.break_condition = True
                    time.sleep(args.break_seconds)
                finally:
                    port.break_condition = False
                time.sleep(0.1)
                port.reset_input_buffer()
            written = port.write(payload)
            port.flush()
            if written != len(payload):
                raise OSError('Incomplete serial write')
            deadline = time.monotonic() + 3.0
            while len(received) < len(payload) and time.monotonic() < deadline:
                received.extend(port.read(max(1, min(port.in_waiting, len(payload)-len(received)))))
    except (OSError, ValueError) as exc:
        error = str(exc)
    passed = bytes(received) == payload and error is None
    report = dict(port=args.port, baud=args.baud, break_seconds=args.break_seconds,
                  tx_bytes=len(payload), rx_bytes=len(received),
                  status='PASS' if passed else 'FAIL', error=error)
    (directory/'tx.bin').write_bytes(payload)
    (directory/'rx.bin').write_bytes(received)
    (directory/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report), flush=True)
    print(f'Saved to {directory}', flush=True)
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
