#!/usr/bin/env python3
"""Capture/parse V3 snapshots and send explicit single-character control commands."""
import argparse
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import time
from m20_fpga import parse_record

def main():
    p=argparse.ArgumentParser(description=__doc__)
    src=p.add_mutually_exclusive_group(required=True);src.add_argument('--port');src.add_argument('--input',type=Path)
    p.add_argument('--baud',type=int,default=115200);p.add_argument('--seconds',type=float,default=60)
    p.add_argument('--command',default='',help='p Pong; s Snake; r reset; space RUN/STOP; n micro-step; 1/2/3 speed while stopped')
    p.add_argument('--output',type=Path)
    p.add_argument('--allow-unrecognized',action='store_true',help='replay raw startup/truncated lines with explicit count, preserving all bytes')
    a=p.parse_args()
    if any(c not in 'psr n123' for c in a.command):p.error('unknown command byte')
    if a.command and a.input:p.error('commands require a serial port')
    root=Path(__file__).resolve().parents[2]
    out=a.output or root/'results/M20_V3'/datetime.now().astimezone().strftime('%Y%m%d_%H%M%S_%f')
    if out.exists():p.error('fresh output directory required')
    out.mkdir(parents=True)
    records=[];invalid=0;sent=False;stream=None;interrupted=False
    def consume(line):
        nonlocal invalid,sent
        try:row=parse_record(line)
        except (ValueError,UnicodeError):invalid+=1;return
        records.append(row)
        if stream and not sent and a.command:
            stream.write(a.command.encode('ascii'));stream.flush();sent=True
        print(f"V3 game={'Snake' if row['game'] else 'Pong'} PC={row['pc']:03X} state={row['ustate']} micro={row['micro']} retired={row['retired']} writes={row['writes']} ticks={row['ticks']} errors={row['errors']} run={row['run']} keys={row['keys']:02X}",flush=True)
    try:
        with (out/'raw.jsonl').open('wb') as raw:
            if a.input:
                for line in a.input.open('rb'):raw.write(line);consume(line)
            else:
                import serial
                stream=serial.Serial(a.port,a.baud,timeout=.1,exclusive=True);stream.reset_input_buffer()
                print('M20_V3_CAPTURE_READY '+str(out),flush=True)
                until=time.monotonic()+a.seconds;pending=bytearray()
                while time.monotonic()<until:
                    chunk=stream.read(max(1,min(stream.in_waiting,4096)))
                    if not chunk:continue
                    raw.write(chunk);raw.flush();pending.extend(chunk)
                    while b'\n' in pending:
                        line,_,pending=pending.partition(b'\n');consume(line)
    except KeyboardInterrupt:interrupted=True
    finally:
        if stream:stream.close()
        fields=['build','game','frame_game','frame_valid','frame_ticks','micro','retired','reads','writes','ticks','errors','pc','ar','a','z','c','gpo','ustate','rom_word','ram_addr','ram_wdata','ram_rdata','ram_ce','ram_oe','ram_we','keys','queued_keys','input_overflows','run','halted','trapped','cycle_ticks','phase_trace','oled_frames']
        with (out/'states.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
            writer.writerows({k:r[k] for k in fields} for r in records)
        for game,name in ((0,'pong'),(1,'snake')):
            rows=[r for r in records if r['frame_valid'] and r['frame_game']==game]
            if rows:(out/f'{name}_latest_ram.memh').write_text(''.join(f'{n:X}\n' for n in rows[-1]['ram_cells']))
        summary=dict(valid_records=len(records),unrecognized_lines=invalid,interrupted=interrupted,
                     commands_sent=a.command if sent else '',last={k:records[-1][k] for k in fields} if records else None,
                     raw_sha256=hashlib.sha256((out/'raw.jsonl').read_bytes()).hexdigest(),
                     errors_observed=max((r['errors'] for r in records),default=None),
                     games_observed=sorted(set(r['game'] for r in records)),
                     time=datetime.now().astimezone().isoformat(),
                     visual_gameplay='NOT_CONFIRMED',storage='FUNCTIONAL_STORAGE' if records and records[-1]['build'].startswith('M20V3F') else 'unknown',
                     frequency_note='50MHz/cycle_ticks is active microcycle rate, not wall-clock throughput while paced/stopped')
        (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('M20_V3_CAPTURE_COMPLETE '+str(out),flush=True)
    return 0 if records and not summary['errors_observed'] and not (a.input and invalid and not a.allow_unrecognized) else 1

if __name__=='__main__':raise SystemExit(main())
