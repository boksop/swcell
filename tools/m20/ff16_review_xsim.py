#!/usr/bin/env python3
"""Emit a frozen-combination-network, two-latch-pair experiment, not a CPU.

The 477 original MUX connections are copied from the hash-checked frozen graph.
Other state bits and memory inputs are held at actual retirement witnesses.
Only the selected source and destination use live double-MUX storage. This
isolates a sensitized real CPU path without running a whole CPU program.
"""
import argparse,csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
NET=ROOT/'rtl/m20/v21/generated/m20v21_cpu_core.netlist.json'

def emit(out):
    out=Path(out);net=json.loads(NET.read_text());vectors=json.loads((out/'cpu_witness_vectors.json').read_text())
    regs=[q for r in net['registers'] for q in r['qbits']];mapping={q:f'qbits[{i}]' for i,q in enumerate(regs)}
    def signal(s):return "1'b"+s if s in ('0','1') else mapping.get(s,s)
    text=['`timescale 1ns/1ps','module ff16_frozen_cone(input wire[32:0]qbits,input wire[15:0]rom_data,input wire[5:0]keys,input wire[3:0]ram_rdata,input wire rst,input real dt,output wire[32:0]dbits);']
    for n in net['nodes']:
        text.append(f'wire {n["id"]};')
        text.append(f'swc_ff16_mux_timing u_{n["id"]}(.s({signal(n["s"])}),.i0({signal(n["i0"])}),.i1({signal(n["i1"])}),.dr(dt),.df(dt),.sr(dt),.sf(dt),.y({n["id"]}),.effective_s());')
    for i,d in enumerate(d for r in net['registers'] for d in r['dbits']):text.append(f'assign dbits[{i}]={signal(d)};')
    text.append('endmodule');(out/'frozen_cone.sv').write_text('\n'.join(text)+'\n')
    with (out/'cone_vectors.txt').open('w') as f:
        for v in vectors:
            initial=v['initial'];packed=sum(initial[q]<<i for i,q in enumerate(regs))
            def bus(name,width):return sum(initial[f'{name}[{i}]']<<i for i in range(width))
            f.write(f'{v["path_id"]} {v["source_index"]} {v["destination_index"]} {packed:x} {v["next_source"]} {v["before_dest_d"]} {bus("rom_data",16):x} {bus("keys",6):x} {bus("ram_rdata",4):x}\n')
    (out/'cone_provenance.json').write_text(json.dumps(dict(netlist_sha256=hashlib.sha256(NET.read_bytes()).hexdigest(),combination_mux=len(net['nodes']),state_scope='two live double-MUX pairs, other31 bits fixed at historical witness; not a fullCPU regression',clock='unchanged actual 20-cell timing model, TAP16',placement='adversarial source leaf0, destination leaf32; illustrative, not PCB assignment',clock_to_q='existing pin-model settled-data SELECT behavior; no extra guaranteed minimum assumed',generated_sv_sha256=hashlib.sha256((out/'frozen_cone.sv').read_bytes()).hexdigest()),indent=2)+'\n')

def check(out):
    out=Path(out)
    with (out/'cone_results.csv').open() as f:rows=list(csv.DictReader(f))
    assert len(rows)==79*4*2
    normal=[r for r in rows if r['chain_stage_ns']=='2.000']
    assert len(normal)==316 and not any(int(r['mismatch']) for r in normal),'unexpected positive control mismatch'
    fast=[r for r in rows if r['chain_stage_ns']=='0.500']
    assert any(int(r['mismatch']) for r in fast),'negative cone witness not observed'
    result={'status':'VERIFIED_LOCAL_CONE_EXPERIMENT','cases':len(rows),'positive_controls':len(normal),'positive_errors':0,'fast_assumed_mismatches':sum(int(r['mismatch']) for r in fast),'physical_status':'NOT_VERIFIED','full_CPU_regression':'NOT_RUN','per_delay':{}}
    for delay in ('0.125','0.250','0.500','1.000'):
        subset=[r for r in fast if r['cell_min_ns']==delay];result['per_delay'][delay]={'paths':len(subset),'mismatches':sum(int(r['mismatch']) for r in subset),'path_ids':[int(r['path_id']) for r in subset if int(r['mismatch'])]}
    (out/'cone_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['emit','check']);p.add_argument('--output',type=Path,required=True);a=p.parse_args();(emit if a.action=='emit' else check)(a.output)
