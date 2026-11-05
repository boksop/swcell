#!/usr/bin/env python3
"""Explicit authorized hardware debug test, leaves CPU running from reset."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import time
import serial
from swcell_m20_v31 import parse_record


def test(port,out):
    out.mkdir(parents=True,exist_ok=False)
    records=[];commands=[]
    with serial.Serial(port,115200,timeout=1,exclusive=True) as link,(out/'raw.jsonl').open('wb') as raw:
        def receive(predicate=lambda r:True):
            deadline=time.monotonic()+10
            while time.monotonic()<deadline:
                line=link.readline()
                if not line:continue
                raw.write(line);raw.flush()
                try:row=parse_record(line)
                except (ValueError,UnicodeError):continue
                records.append(row|dict(host_monotonic=time.monotonic()))
                if row['errors']!=0:raise AssertionError('CPU cycle contract errors')
                if predicate(row):return row
            raise TimeoutError('V3.1 telemetry timeout')
        def send(command):
            commands.append(dict(command=command,host_monotonic=time.monotonic()))
            link.write(command.encode('ascii'));link.flush()
        initial=receive()
        if initial['run']:send(' ')
        stopped=receive(lambda r:not r['run'] and not r['active'])
        again=receive(lambda r:not r['run'] and not r['active'])
        for field in ('micro','writes','retired','pc','ar','a','gpo','ustate'):
            assert again[field]==stopped[field],('STOP',field)
        send('n');stepped=receive(lambda r:r['micro']==stopped['micro']+1 and not r['active'])
        assert not stepped['run'] and stepped['retired']-stopped['retired'] in (0,1)
        send('r');reset=receive(lambda r:r['pc']==0 and r['ustate']==1 and not r['active'] and not r['cpu_reset'])
        assert reset['gpo']==8 and not reset['run']
        assert reset['writes']==stepped['writes'],'reset unexpectedly wrote RAM'
        send(' ');resumed=receive(lambda r:r['run'] and r['active'] and r['retired']>reset['retired'])
        later=receive(lambda r:r['micro']>resumed['micro'])
        assert later['run'] and not later['halted'] and not later['trapped']
    result=dict(status='PASS',scope='UART debug STOP/STEP/RESET/resume only; not human OLED/key acceptance',
                records=len(records),commands=commands,initial=initial,stopped=stopped,stepped=stepped,
                reset=reset,resumed=resumed,later=later,date=datetime.now().astimezone().isoformat())
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();test(a.port,a.output)
