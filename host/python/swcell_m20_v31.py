#!/usr/bin/env python3
"""Generic V3.1 CPU UART telemetry: live serial capture or offline JSONL decode."""
import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import re
import sys
import time

WIDTHS=dict(pc=3,ar=2,a=1,gpo=1,ustate=1,keys=2,flags=2,
            micro=16,retired=16,reads=16,writes=16,errors=16)


def parse_record(line):
    row=json.loads(line)
    if not isinstance(row,dict) or row.get('type')!='M20_V31_STATE':raise ValueError('not V3.1 telemetry')
    if row.get('build')!='M20V31A01':raise ValueError('unknown V3.1 build')
    result=dict(type=row['type'],build=row['build'])
    for key,width in WIDTHS.items():
        value=row.get(key)
        if not isinstance(value,str) or not re.fullmatch(f'[0-9A-Fa-f]{{{width}}}',value):raise ValueError(f'invalid {key}')
        result[key]=int(value,16)
    if result['keys']>63 or result['ustate']>7 or result['flags']>127:raise ValueError('reserved bits set')
    for bit,name in enumerate(('c','z','trapped','halted','cpu_reset','run','active')):
        result[name]=bool(result['flags']&(1<<bit))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True);group.add_argument('--input',type=Path);group.add_argument('--port')
    p.add_argument('--baud',type=int,default=115200);p.add_argument('--output',type=Path)
    p.add_argument('--seconds',type=float,help='Optional bounded live capture duration')
    args=p.parse_args()
    if args.seconds is not None and args.seconds<=0:p.error('--seconds must be positive')
    out=args.output or Path('results/M20_V31')/datetime.now().astimezone().strftime('%Y%m%d_%H%M%S%z')
    out.mkdir(parents=True,exist_ok=False)
    serial=None;source=None;count=bad=0
    try:
        if args.port:
            import serial as pyserial
            serial=pyserial.Serial(args.port,args.baud,timeout=1,exclusive=True);source=serial
        else:source=args.input.open('rb')
        with (out/'raw.jsonl').open('wb') as raw,(out/'states.csv').open('w',newline='') as dst:
            writer=None
            started=time.monotonic()
            while args.seconds is None or time.monotonic()-started<args.seconds:
                line=source.readline()
                if not line:
                    if serial is None:break
                    continue
                raw.write(line);raw.flush()
                try:row=parse_record(line)
                except (ValueError,UnicodeError) as exc:
                    bad+=1;print(f'UART warning: {exc}',file=sys.stderr);continue
                if writer is None:writer=csv.DictWriter(dst,fieldnames=list(row));writer.writeheader()
                writer.writerow(row);dst.flush();count+=1
                if serial is not None:print(f"PC={row['pc']:03X} retired={row['retired']} errors={row['errors']}",flush=True)
    except KeyboardInterrupt:pass
    finally:
        if source is not None:source.close()
        (out/'summary.json').write_text(json.dumps(dict(records=count,invalid_lines=bad,hardware_observation=bool(serial)),indent=2)+'\n')
    if not count:raise SystemExit('No valid telemetry records')
    print(f'V31_CAPTURE_PASS records={count} invalid={bad} {out}')


if __name__=='__main__':main()
