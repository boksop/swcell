#!/usr/bin/env python3
"""Explicit real-board RUN/STEP/RESET/speed test. Requires release of all keys.

Only UART controls and observations: the PC does not write game RAM or compute
updates for the FPGA. The independent ISA machine is a read-only oracle.
"""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import time
import serial
from m20 import Machine,assemble
from m20_fpga import parse_record

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',default='/dev/ttyUSB1');p.add_argument('--output',type=Path,required=True)
    p.add_argument('--snake-source',type=Path,help='explicit assembled software variant; default is frozen original Snake')
    p.add_argument('--snake-ticks',type=int,default=128,help='minimum completed Snake ticks compared against the ISA oracle')
    p.add_argument('--leave-snake',action='store_true',help='keep the tested Snake game visible after successful verification')
    a=p.parse_args();out=a.output
    if a.snake_ticks<1:p.error('--snake-ticks must be positive')
    if out.exists():p.error('fresh output required')
    out.mkdir(parents=True);root=Path(__file__).resolve().parents[2]
    records=[];commands=[];checks=[];invalid=0;pending=bytearray();last=None;error=None
    stream=serial.Serial(a.port,115200,timeout=.1,exclusive=True)
    raw=(out/'raw.jsonl').open('wb')
    def receive(predicate=lambda r:True,timeout=10):
        nonlocal pending,last,invalid
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            while b'\n' in pending:
                line,_,pending=pending.partition(b'\n')
                try:r=parse_record(line)
                except (ValueError,UnicodeError):invalid+=1;continue
                records.append(r);last=r
                print(f"CONTROL game={r['game']} run={r['run']} active={r['active']} micro={r['micro']} writes={r['writes']} tick={r['ticks']} errors={r['errors']} divider={r['cycle_ticks']}",flush=True)
                if r['build'] not in ('M20V3F02','M20V3F03','M20V3F04','M20V3F05','M20V3F06'):continue
                if r['keys']!=0:raise RuntimeError('release all physical keys for zero-input control test')
                if r['errors']:raise RuntimeError('FPGA instruction cycle error')
                if predicate(r):return r
            chunk=stream.read(max(1,min(stream.in_waiting,4096)))
            if chunk:raw.write(chunk);raw.flush();pending.extend(chunk)
        raise TimeoutError('matching V3 telemetry timed out')
    def send(ch):
        stream.write(ch.encode());stream.flush();commands.append(dict(command=ch,time=datetime.now().astimezone().isoformat()))
    def run(value):
        r=receive()
        if r['run']!=value:send(' ')
        return receive(lambda x:x['run']==value and (value or not x['active']))
    try:
        receive(timeout=30)
        stopped=run(0);again=receive()
        assert (again['micro'],again['writes'],again['pc'],again['ustate'])==(stopped['micro'],stopped['writes'],stopped['pc'],stopped['ustate'])
        checks.append(dict(test='STOP',status='PASS',micro=again['micro'],writes=again['writes']))
        send('n');step=receive(lambda r:r['micro']==again['micro']+1 and not r['active'])
        assert step['run']==0
        checks.append(dict(test='STEP_ONE_MICROCYCLE',status='PASS',before=again['micro'],after=step['micro']))
        send('r');r=receive(lambda r:not r['active'] and not r['reset'] and r['ustate']==1 and r['pc']==0)
        assert (r['ar'],r['a'],r['z'],r['c'],r['gpo'],r['run'])==(0,0,1,0,8,0)
        checks.append(dict(test='RESET_WHILE_STOPPED',status='PASS'))
        for command,divider in (('1',500),('2',100),('3',50)):
            run(0);send(command);receive(lambda r:r['cycle_ticks']==divider)
            run(1);before=receive();after=receive()
            assert after['micro']>before['micro'] and after['retired']>before['retired']
            checks.append(dict(test='ACTIVE_RATE',status='PASS',divider=divider,rate_hz=50000000//divider,
                               observed_micro_delta=after['micro']-before['micro']))
        run(0);send('s');selected=receive(lambda r:r['game']==1 and not r['reset'] and not r['active'])
        base=selected['ticks'];run(1)
        snake_source=a.snake_source or root/'software/m20_300/snake.asm'
        asm=assemble(snake_source.read_text());machine=Machine(asm.words,keys=0,trace=False)
        local_tick=0;compared=0
        while local_tick<a.snake_ticks:
            r=receive(lambda r:r['game']==1 and r['frame_valid'] and r['frame_game']==1,timeout=15)
            target=r['frame_ticks']-base
            while local_tick<target:
                if local_tick:machine.step()
                for _ in range(20000):
                    if machine.pc==asm.symbols['tick_done']:break
                    assert machine.step() is not None
                else:raise RuntimeError('ISA oracle exceeded bound')
                local_tick+=1
            assert r['ram_cells']==machine.ram,('Snake snapshot differs',local_tick)
            compared+=1
        checks.append(dict(test='SNAKE_ZERO_KEY_RAM_ORACLE',status='PASS',last_local_tick=local_tick,
                           complete_ram_snapshots=compared,cells_per_snapshot=256,
                           source=str(snake_source),source_sha256=hashlib.sha256(snake_source.read_bytes()).hexdigest()))
        if not a.leave_snake:
            send('p');restored=receive(lambda r:r['game']==0 and r['run']==1 and r['frame_valid'] and r['frame_game']==0)
            checks.append(dict(test='RESTORE_ORIGINAL_PONG',status='PASS',retired=restored['retired']))
    except Exception as exc:
        error=repr(exc)
        # Preserve the failure and request a usable original-game state.
        try:
            send('p')
            if last and not last['run']:send(' ')
        except Exception:pass
    finally:
        stream.close();raw.close()
        summary=dict(status='FAIL' if error else 'PASS',error=error,checks=checks,commands=commands,
                     valid_records=len(records),unrecognized_lines=invalid,
                     last={k:v for k,v in last.items() if k not in ('ram_cells','ram')} if last else None,
                     raw_sha256=hashlib.sha256((out/'raw.jsonl').read_bytes()).hexdigest(),
                     limits='UART controls/complete RAM comparisons; no manual OLED/button gameplay confirmation')
        (out/'verification.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('M20_V3_HARDWARE_CONTROL_'+summary['status'],str(out),flush=True)
    return 1 if error else 0

if __name__=='__main__':raise SystemExit(main())
