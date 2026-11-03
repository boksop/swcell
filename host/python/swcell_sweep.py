#!/usr/bin/env python3
"""Static-bitstream M11 sweep: build -> JTAG -> serial -> independent windows -> long PRBS.

Each bitstream is timing checked before programming. Flash is never accessed.
"""
from __future__ import annotations
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from swcell_capture import parse_record
from swcell_hs import FIELDS, HighSpeedAnalysis

ROOT=Path(__file__).resolve().parents[2]
FREQUENCIES=(1000000,5000000,10000000,25000000,50000000,75000000,100000000,125000000,150000000,200000000)

def fingerprint():
    paths=[*ROOT.glob('rtl/common/**/*.sv'),*ROOT.glob('rtl/modules/m11/phase2/*.sv'),
           *ROOT.glob('fpga/xc7k325t/phase2/*'),ROOT/'fpga/xc7k325t/constraints/board_50mhz.xdc']
    h=hashlib.sha256()
    for path in sorted(paths):
        if path.is_file():h.update(str(path.relative_to(ROOT)).encode());h.update(path.read_bytes())
    return h.hexdigest()

def terminate(process):
    if process.poll() is None:
        try:os.killpg(process.pid,signal.SIGTERM)
        except ProcessLookupError:return
        try:process.wait(timeout=10)
        except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()

def build_point(point,args):
    hz,q,m,bits,pattern,scan=point
    source_id=fingerprint()
    key=f'f{hz}_q{q}_m{m}_n{bits}_p{pattern}_s{scan}_{source_id[:12]}'
    out=ROOT/'build/phase2/images'/key;out.mkdir(parents=True,exist_ok=True)
    status=out/'build_status.json'
    bit=out/'swcell_m11_hs_top.bit'
    provenance=out/'source_manifest.json'
    if status.exists() and not args.rebuild:
        state=json.loads(status.read_text())
        if state['status']=='UNSUPPORTED':return out,state
        if state['status']=='SUPPORTED' and bit.exists() and provenance.exists():
            saved=json.loads(provenance.read_text())
            digest=hashlib.sha256(bit.read_bytes()).hexdigest()
            if saved.get('source_sha256')==source_id and saved.get('point')==list(point) and saved.get('bitstream_sha256',digest)==digest:
                # Backfill the hash for pre-integrity-check cache entries.
                saved['bitstream_sha256']=digest
                provenance.write_text(json.dumps(saved,indent=2)+'\n')
                return out,state
    # A failed/interrupted rebuild must not leave an old SUPPORTED marker valid.
    status.unlink(missing_ok=True)
    command=[args.vivado,'-mode','batch','-nojournal','-log',str(out/'vivado.log'),
             '-source',str(ROOT/'fpga/xc7k325t/phase2/build_hs.tcl'),'-tclargs',
             *map(str,(hz,q,m,bits,pattern,scan)),str(out)]
    print('BUILD',key,flush=True)
    with (out/'console.log').open('wb') as log:
        process=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:code=process.wait(timeout=args.build_timeout)
        except BaseException:terminate(process);raise
    if fingerprint()!=source_id:
        state={'status':'BUILD_ERROR','reason':'SOURCE_CHANGED_DURING_BUILD'}
    elif code:
        state={'status':'BUILD_ERROR','reason':f'Vivado exit {code}; {out}/console.log'}
    elif status.exists():state=json.loads(status.read_text())
    else:state={'status':'BUILD_ERROR','reason':'Missing build status'}
    status.write_text(json.dumps(state,indent=2)+'\n')
    saved={'source_sha256':source_id,'point':point}
    if state['status']=='SUPPORTED' and bit.exists():saved['bitstream_sha256']=hashlib.sha256(bit.read_bytes()).hexdigest()
    provenance.write_text(json.dumps(saved,indent=2)+'\n')
    return out,state

def host_record(point,status,reason):
    hz,q,m,bits,pattern,scan=point
    r={name:0 for name in FIELDS}
    r.update(protocol_version=2,module='M11',device='74LVC1G157',source='host',
             type='PHASE_RESULT' if scan else 'FREQ_RESULT',test='PRBS_STABILITY' if pattern==5 else 'DFF_HS_PATTERN',
             frequency_hz=hz,d_phase=4,q_sample_phase=q,qm_sample_phase=m,
             d_phase_mdeg=93600 if hz==1000000 else 90000,
             q_phase_mdeg=((q*50+8)//16)*7200 if hz==1000000 else q*22500,
             qm_phase_mdeg=((m*50+8)//16)*7200 if hz==1000000 else m*22500,
             pattern=pattern,requested_bits=bits,status=status,reason=reason,
             voltage_v=None,temperature_c=None,pcb_delay_ns=None)
    return r

def run_hardware(point,out,args,raw,analysis):
    import serial
    hz,q,m,bits,pattern,scan=point
    records=[];pending=bytearray();invalid=0
    # Open before programming, and read while Vivado runs: no 4KiB tty overflow.
    with serial.Serial(args.port,args.baud,timeout=.1,exclusive=True) as stream, (out/'program.console.log').open('wb') as log:
        command=[args.vivado,'-mode','batch','-nojournal','-log',str(out/'program.log'),
                 '-source',str(ROOT/'fpga/xc7k325t/scripts/program.tcl'),'-tclargs',
                 str(out/'swcell_m11_hs_top.bit'),args.device]
        process=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        deadline=time.monotonic()+args.program_timeout+bits/hz+5
        complete=False
        try:
            while time.monotonic()<deadline:
                chunk=stream.read(max(1,min(stream.in_waiting,4096)))
                if chunk:
                    raw.write(chunk);raw.flush();pending.extend(chunk)
                    while b'\n' in pending:
                        line,_,pending=pending.partition(b'\n')
                        try:r=parse_record(line)
                        except (ValueError,UnicodeError,TypeError) as e:
                            invalid+=1;print('UART invalid:',str(e),flush=True);continue
                        if r.get('protocol_version')!=2:continue
                        identity=tuple(r[k] for k in ('frequency_hz','q_sample_phase','qm_sample_phase','requested_bits','pattern'))
                        if identity!=(hz,q,m,bits,pattern):continue
                        analysis.add(r);records.append(r)
                        if r['type']=='SWEEP_COMPLETE':complete=True
                    if len(pending)>8192:invalid+=1;pending.clear()
                if complete and process.poll() is not None:break
                if process.poll() not in (None,0):raise RuntimeError('JTAG programming failed')
            if not complete or process.poll() is None:raise TimeoutError('JTAG/UART point timeout')
            expected_type='PHASE_RESULT' if scan else 'FREQ_RESULT'
            kinds=[r['type'] for r in records]
            if not kinds or kinds[0]!='SWEEP_START' or kinds[-1]!='SWEEP_COMPLETE' or kinds.count(expected_type)!=1 or invalid:
                raise RuntimeError('Incomplete/contaminated UART point; retain raw data and retry after quiescing')
            result=next(r for r in records if r['type']==expected_type)
            if result['status']=='ABORTED':raise RuntimeError('Clock lock lost or hardware timeout')
            print('RESULT',hz,q,m,result['status'],f"Q={result['q_errors']}/{bits}",f"QM={result['qm_errors']}/{bits}",flush=True)
            return result
        finally:terminate(process)

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--frequencies',default=','.join(map(str,FREQUENCIES)))
    p.add_argument('--phases',default=','.join(map(str,range(16))))
    p.add_argument('--scan-bits',type=int,default=4096)
    p.add_argument('--long-bits',type=int,default=1000000)
    p.add_argument('--important-frequencies',default='')
    p.add_argument('--important-bits',type=int,default=100000000)
    p.add_argument('--patterns',default='5',help='0=zero,1=one,2=0101,3=0011,5=PRBS31')
    p.add_argument('--minimum-window-bins',type=int,default=3)
    p.add_argument('--build-only',action='store_true')
    p.add_argument('--point',nargs=2,type=int,metavar=('Q','QM'),help='Single selected pair; uses --long-bits, no scan')
    p.add_argument('--port',default='/dev/ttyUSB1');p.add_argument('--baud',type=int,default=115200)
    p.add_argument('--device',default='xc7k325t_0');p.add_argument('--vivado',default='vivado')
    p.add_argument('--output',type=Path);p.add_argument('--rebuild',action='store_true')
    p.add_argument('--build-timeout',type=int,default=1800);p.add_argument('--program-timeout',type=int,default=120)
    args=p.parse_args(argv)
    try:
        frequencies=list(map(int,args.frequencies.split(',')));phases=list(map(int,args.phases.split(',')))
        patterns=list(map(int,args.patterns.split(',')));important=set(map(int,filter(None,args.important_frequencies.split(','))))
    except ValueError:p.error('Frequencies/phases/patterns must be comma-separated integers')
    if any(not 1<=n<=1000000000 for n in (args.scan_bits,args.long_bits,args.important_bits)):p.error('Counts must be 1..1e9')
    if args.long_bits<1000000 and not args.build_only:p.error('Long runs require >=1e6 bits')
    if args.important_bits<1000000 and not args.build_only:p.error('Important runs require >=1e6 bits')
    if args.baud!=115200:p.error('Current static build profile uses UART 115200; receiver baud must match')
    if any(x<=0 for x in frequencies) or len(set(frequencies))!=len(frequencies):p.error('Invalid/duplicate frequencies')
    if any(x not in range(16) for x in phases) or len(set(phases))!=len(phases):p.error('Invalid/duplicate phases')
    if any(x not in (0,1,2,3,5) for x in patterns):p.error('Invalid pattern')
    if args.point and any(x not in range(16) for x in args.point):p.error('Invalid selected phase')
    if not 1<=args.minimum_window_bins<=16:p.error('Invalid minimum window width')
    output=args.output or ROOT/'results/M11'/datetime.now().astimezone().strftime('%Y%m%d_%H%M%S_%f%z')
    output.mkdir(parents=True,exist_ok=False)
    config={k:str(v) if isinstance(v,Path) else v for k,v in vars(args).items()}
    (output/'metadata.json').write_text(json.dumps(dict(config=config,source_sha256=fingerprint(),
        device='xc7k325tffg900-2',voltage_v=None,voltage_nominal_v=3.3,temperature_c=None,
        started_at=datetime.now().astimezone().isoformat()),indent=2)+'\n')
    print('OUTPUT',output,flush=True)
    analysis=HighSpeedAnalysis(args.minimum_window_bins);manifest=[];failures=0;measurement_failures=0
    run_status='COMPLETE'
    try:
        with (output/'raw.jsonl').open('wb') as raw, (output/'host_events.jsonl').open('wb') as host_log:
            def point(h,q,m,n,pattern,scan):
                nonlocal failures,measurement_failures
                values=(h,q,m,n,pattern,scan)
                out,status=build_point(values,args)
                entry=dict(point=values,build_dir=str(out),**status)
                manifest.append(entry)
                (output/'runner_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
                if status['status']!='SUPPORTED':
                    r=host_record(values,status['status'],status['reason']);analysis.add(r)
                    host_log.write((json.dumps(r)+'\n').encode());host_log.flush()
                    print('SKIP',h,q,m,status,flush=True)
                    if status['status']=='BUILD_ERROR':failures+=1
                    return None
                entry['bitstream_sha256']=hashlib.sha256((out/'swcell_m11_hs_top.bit').read_bytes()).hexdigest()
                if args.build_only:return None
                try:
                    result=run_hardware(values,out,args,raw,analysis)
                    if not scan and result['status']!='PASS':measurement_failures+=1
                    return result
                except (RuntimeError,TimeoutError,OSError) as e:
                    failures+=1;r=host_record(values,'TRANSPORT_ERROR',str(e));analysis.add(r)
                    host_log.write((json.dumps(r)+'\n').encode());host_log.flush();print('POINT ERROR',str(e),flush=True)
                    return None
                finally:
                    (output/'runner_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
                    analysis.save(output,plots=False)
            for hz in frequencies:
                if args.point:
                    for pattern in patterns:point(hz,*args.point,args.long_bits,pattern,0)
                    continue
                for phase in phases:point(hz,phase,phase,args.scan_bits,5,1)
                if args.build_only:continue
                windows=analysis.windows(args.minimum_window_bins).get(str(hz))
                if not windows or windows['status']!='WINDOW_FOUND':
                    scanned=[r for r in analysis.records if r['type']=='PHASE_RESULT' and r['frequency_hz']==hz]
                    valid=any(r['status'] in ('PASS','CAPTURE_ERRORS') for r in scanned)
                    if valid:measurement_failures+=1
                    if scanned and all(r['status']=='UNSUPPORTED' for r in scanned):state='UNSUPPORTED'
                    elif any(r['status']=='BUILD_ERROR' for r in scanned):state='BUILD_ERROR'
                    elif any(r['status'] in ('TRANSPORT_ERROR','ABORTED') for r in scanned):state='TRANSPORT_ERROR'
                    else:state='NO_VALID_CAPTURE_WINDOW'
                    r=host_record((hz,0,0,args.long_bits,5,0),state,'SCAN_SUMMARY: no selected phase; no long-run samples executed')
                    r['test']='SCAN_SUMMARY';r['selection_valid']=False
                    analysis.add(r);host_log.write((json.dumps(r)+'\n').encode());host_log.flush()
                    print(state,hz,flush=True);continue
                q=windows['q']['center'];m=windows['qm']['center']
                n=args.important_bits if hz in important else args.long_bits
                for pattern in patterns:point(hz,q,m,n,pattern,0)
    except KeyboardInterrupt:
        run_status='INTERRUPTED'
        print('Interrupted: raw data and partial analysis retained',flush=True);return 130
    except (OSError,subprocess.TimeoutExpired,ValueError) as exc:
        run_status='INFRASTRUCTURE_ERROR';failures+=1
        print('Sweep infrastructure error:',str(exc),flush=True);return 2
    finally:
        summary=analysis.save(output)
        summary.update(runner_status=run_status,infrastructure_errors=failures,measurement_failures=measurement_failures)
        (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        (output/'runner_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return 2 if failures else (1 if measurement_failures else 0)

if __name__=='__main__':raise SystemExit(main())
