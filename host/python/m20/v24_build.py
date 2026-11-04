"""Pure157 autonomous generator; independent of the frozen CPU generator."""
import argparse,json,hashlib
from pathlib import Path
from .v2_muxlib import Circuit
ROOT=Path(__file__).resolve().parents[3]
NAMES=['j0','j1','j2','j3','run1','run2','step1','step2','token','ack','active','step_mode','fault_reg']

def generate(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);c=Circuit(optimize=True)
 def mux(s,a,b):return c.mux(s,a,b,group='control')
 def inv(a):return c.inv(a,group='control')
 def AND(*v):return c.reduce_and(v,group='control')
 def OR(*v):return c.reduce_or(v,group='control')
 def eq(v,n):return c.eq_const(v,n,group='decode')
 j=NAMES[:4];safe=eq(j,8)
 valid=OR(*(eq(j,n) for n in (0,1,3,7,15,14,12,8)))
 bad=OR(inv(valid),AND(inv('active'),inv(safe)))
 pending=c.xor_('step2','token',group='control')
 stepwant=AND(inv('run2'),pending);want=OR('run2',pending)
 complete=AND('active',safe,'step_mode')
 atstart=AND(safe,inv('fault_reg'),inv(bad),mux(complete,want,'run2'))
 accept=AND(atstart,stepwant,inv(complete))
 # No multi-bit repair on the fault-detection edge: clamp first, repair a cycle later.
 advance=AND(inv('fault_reg'),inv(bad),OR(AND('active',inv(safe)),atstart))
 d={}
 shifted=[inv('j3'),'j0','j1','j2']
 for i,n in enumerate(j):d[n]=mux('fault_reg',mux(advance,n,shifted[i]),int(i==3))
 d['run1']='run_request';d['run2']='run1';d['step1']='step_request';d['step2']='step1'
 d['token']=mux(accept,'token','step2')
 d['ack']=mux(complete,'ack','token')
 d['active']=mux(OR('fault_reg',bad),mux(safe,'active',atstart),0)
 # At a boundary complete the old step before considering new continuous RUN.
 d['step_mode']=mux(OR('fault_reg',bad),mux(safe,'step_mode',AND(atstart,stepwant,inv(complete))),0)
 d['fault_reg']=OR('fault_reg',bad)
 for n in NAMES:d[n]=mux('rst',d[n],int(n=='j3'))
 rawh=OR('j3','j2');raws=AND('j3','j2');blocked=OR('rst','fault_reg',inv('active'))
 outputs=dict(master_hold=mux(blocked,rawh,1),slave_open=mux(blocked,raws,0),busy='active',step_ack='ack',fault='fault_reg')
 def b(v):return f"1'b{v}" if isinstance(v,int) else v
 lines=['`timescale 1ns/1ps','`default_nettype none','module swc157_phasegen_v24 #(',
 ' parameter real COMB_NS=0,INTERLOCK_NS=0,LOCAL_DATA_NS=0,LOCAL_SELECT_NS=0,LOCAL_MASTER_NS=0,LOCAL_SLAVE_NS=0,LOCAL_SKEW_NS=0,',
 ' parameter bit CHECK_FATAL=1',') (input wire clk_ref,rst,run_request,step_request,',
 ' output wire master_hold,slave_open,busy,step_ack,fault,',
 ' output wire [3:0] phase_state,output wire local_h,local_s);']
 lines += [' wire '+','.join(NAMES)+';']
 for n in c.nodes:lines.append(f' wire {n["id"]};')
 lines += [' // Causal local interlock; no assumed absolute physical dead time.',
 ' swc_mux157_v23 #(.DATA_NS(INTERLOCK_NS),.SELECT_NS(INTERLOCK_NS)) clock_h(.s(clk_ref),.i0(local_s),.i1(1\'b1),.y(local_h));',
 ' swc_mux157_v23 #(.DATA_NS(INTERLOCK_NS),.SELECT_NS(INTERLOCK_NS)) clock_s(.s(clk_ref),.i0(1\'b0),.i1(local_h),.y(local_s));']
 for n in c.nodes:lines.append(f' swc_mux157_v23 #(.DATA_NS(COMB_NS),.SELECT_NS(COMB_NS)) u_{n["id"]}(.s({b(n["s"])}),.i0({b(n["i0"])}),.i1({b(n["i1"])}),.y({n["id"]}));')
 for i,n in enumerate(NAMES):
  lines.append(f' swc_ms_bit_v23 #(.DATA_NS(LOCAL_DATA_NS),.SELECT_NS(LOCAL_SELECT_NS),.MASTER_NS(LOCAL_MASTER_NS+{i%3}*LOCAL_SKEW_NS),.SLAVE_NS(LOCAL_SLAVE_NS+{(i+1)%3}*LOCAL_SKEW_NS),.CHECK_FATAL(CHECK_FATAL)) r{i}(.master_hold(local_h),.slave_open(local_s),.d({b(d[n])}),.q({n}),.qm(),.checks_enable(!rst));')
 for n,v in outputs.items():lines.append(f' assign {n}={b(v)};')
 lines+=[' assign phase_state={j3,j2,j1,j0};','endmodule','`default_nettype wire']
 text='\n'.join(lines)+'\n';(out/'swc157_phasegen_v24.sv').write_text(text)
 manifest=dict(schema=1,nodes=c.nodes,state_names=NAMES,d=d,outputs=outputs,comb_mux=len(c.nodes),local_interlock_mux=2,storage_bits=13,storage_mux=26,total_mux=len(c.nodes)+28,source_sha256=hashlib.sha256(text.encode()).hexdigest(),classification='Digital model only; physical minimum timing uncharacterized')
 (out/'swc157_phasegen_v24.json').write_text(json.dumps(manifest,indent=2)+'\n');print('V24_GENERATED',manifest['total_mux']);return manifest,c
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'rtl/m20/v24/generated');a=p.parse_args();generate(a.output)
