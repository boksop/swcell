"""Independent pin/body/state binding audit; does not import the generator."""
import json,re,hashlib
from pathlib import Path
from .ff16_structure import audit as audit_phase
from .v2_audit import vector
ROOT=Path(__file__).resolve().parents[3]
def audit(core=None):
 core=Path(core or ROOT/'rtl/m20/v24_ffcd/generated/m20ffcd_cpu_core.sv');text=core.read_text()
 base=(ROOT/'rtl/m20/v23/generated/m20v23_cpu_core.sv').read_text()
 net=json.loads((ROOT/'rtl/m20/v21/generated/m20v21_cpu_core.netlist.json').read_text())
 boundary='    wire [32:0] state_q,state_qm,state_d,state_me,state_se;'
 assert text.count(boundary)==1
 body,binding=text.split(boundary)
 assert body.split(');',1)[1]==base.split('    wire [32:0] state_q,state_qm,state_d;')[0].split(');',1)[1], 'frozen combinational body changed'
 assert body.count('swc_mux157_v23 #(')==477
 q=[q for reg in net['registers'] for q in reg['qbits']];d=[d for reg in net['registers'] for d in reg['dbits']]
 aliases=re.findall(r'assign ([\w\[\]]+)=state_q\[(\d+)\];',binding)
 assert aliases==[(q,str(i)) for i,q in enumerate(q)],'Q alias changed'
 assert vector(re.search(r'assign state_d=([^;]+);',binding)[1])==d
 ideal,latch=binding.split('end else if(STATE_IMPL=="TWO_PHASE_LATCH") begin:g_latch')
 assert 'always_ff' not in latch and 'always_latch' not in latch,'hidden native CPU state'
 for q,i in aliases:ideal=ideal.replace(f'    assign {q}=state_q[{i}];','')
 ideal=re.sub(r'    assign state_d=[^;]+;','',ideal)
 expression='{'+','.join("1'b"+v if v in ('0','1') else v for v in reversed(d))+'}'
 normalize=lambda s:re.sub(r'\s+','',s)
 assert normalize(ideal)==normalize('generate if(STATE_IMPL=="IDEAL_FF") begin:g_ideal logic [32:0] state_ff; always_ff @(posedge clk) state_ff <= '+expression+'; assign state_q=state_ff;assign state_qm=state_ff;')
 expected=''
 for i,dbit in enumerate(d):
  expected+=f'swc_ffcd_ms_bit #(.INDEX({i}),.LOGIC_ONLY(LOGIC_ONLY)) b{i}(.master_hold(master_hold),.slave_open(slave_open),.d({dbit}),.q(state_q[{i}]),.qm(state_qm[{i}]),.checks_enable(checks_enable),.me(state_me[{i}]),.se(state_se[{i}]));'
 expected+='end else begin:g_bad initial $fatal(1,"unknown state implementation");end endgenerate endmodule `default_nettype wire'
 assert normalize(latch)==normalize(expected),'state binding or hidden logic changed'
 pair=(ROOT/'sim/m20_ff16/swc_ff16_timing.sv').read_text().split('module swc_ff16_latch_pair',1)[1].split('endmodule',1)[0]
 assert pair.count('swc_ff16_mux_timing')==2 and '.i0(d),.i1(qm)' in pair and '.i0(q),.i1(qm)' in pair
 assert 'always_ff' not in pair and 'always_latch' not in pair
 phase=audit_phase(tap_stages=16);assert phase['physical_mux_count']==20
 return dict(status='VERIFIED',comb_mux=477,state_bits=33,storage_mux=66,cpu_total=543,generator_mux=20,total_excluding_buffers=563,
             physical_timing='NOT_VERIFIED',native_ff_in_cpu_latch_branch=0,fpga_control_and_memories='EXCLUDED_FROM_EXTERNAL_157_BUDGET',
             generated_sv_sha256=hashlib.sha256(text.encode()).hexdigest(),method='exact frozen combinational body, independent D/Q/QM aliases, exact storage-only branch, pair topology, fixed20 audit')
