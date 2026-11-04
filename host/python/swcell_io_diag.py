#!/usr/bin/env python3
"""Capture/replay the independent SSD1306/key diagnostic JSONL, preserving raw input."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import time
from io_diag import parse_record, StateCollector


def main():
    p = argparse.ArgumentParser(description=__doc__)
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument('--input', type=Path)
    source.add_argument('--port')
    p.add_argument('--baud', type=int, default=115200)
    p.add_argument('--duration', type=float, default=180)
    p.add_argument('--output', type=Path)
    p.add_argument('--require-fpga-coverage', action='store_true')
    p.add_argument('--probe-rx', action='store_true', help='send one harmless0x55 burst after first diagnostic record')
    args = p.parse_args()
    root = Path(__file__).resolve().parents[2]
    out = args.output or root / 'results/BOARD_IO' / datetime.now().astimezone().strftime('%Y%m%d_%H%M%S_%f%z')
    if out.exists():
        p.error('output directory must be fresh')
    out.mkdir(parents=True)
    collector = StateCollector()
    invalid = 0
    stream = None
    probe_sent = False
    interrupted = False
    def consume(line):
        nonlocal invalid, probe_sent
        try:
            state = parse_record(line)
        except (ValueError, UnicodeError) as error:
            invalid += 1
            if invalid <= 8:
                print('UNRECOGNIZED:', str(error), flush=True)
            return
        collector.add(state)
        if stream and args.probe_rx and not probe_sent:
            stream.write(b'\x55'*8)
            probe_sent = True
        print(f"IO keys={state['keys']:03X} seen={state['seen']:03X} events={state['events']} mode={state['mode']} patterns={state['patterns']:02X} frame={state['frame']} oled_tx_ready={state['oled']} rx={state['rx']}", flush=True)
    try:
        with (out / 'raw.jsonl').open('wb') as raw:
            if args.input:
                with args.input.open('rb') as incoming:
                    for line in incoming:
                        raw.write(line)
                        consume(line)
            else:
                import serial
                stream = serial.Serial(args.port, args.baud, timeout=.1, exclusive=True)
                stream.reset_input_buffer()
                print('IO_CAPTURE_READY ' + str(out), flush=True)
                until = time.monotonic() + args.duration
                pending = bytearray()
                while time.monotonic() < until:
                    block = stream.read(max(1, min(stream.in_waiting, 4096)))
                    if not block:
                        continue
                    raw.write(block)
                    raw.flush()
                    pending.extend(block)
                    while b'\n' in pending:
                        line, _, pending = pending.partition(b'\n')
                        consume(line)
    except KeyboardInterrupt:
        interrupted = True
    finally:
        if stream:
            stream.close()
        collector.save(out)
        raw_path = out / 'raw.jsonl'
        meta = dict(time=datetime.now().astimezone().isoformat(), port=args.port, baud=args.baud,
                    input=str(args.input) if args.input else None, interrupted=interrupted,
                    unrecognized_lines=invalid, rx_probe_sent=probe_sent,
                    raw_sha256=hashlib.sha256(raw_path.read_bytes()).hexdigest() if raw_path.exists() else None,
                    physical_oled_or_led_confirmed=False)
        (out / 'metadata.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2)+'\n')
    summary = collector.summary()
    print('IO_CAPTURE_COMPLETE ' + json.dumps(summary), flush=True)
    if not collector.rows or (args.input and invalid):
        return 1
    if args.require_fpga_coverage and not (summary['all_inputs_seen_by_fpga'] and summary['all_patterns_transmitted']):
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
