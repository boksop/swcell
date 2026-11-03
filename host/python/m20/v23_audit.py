"""Independent state-binding audit against frozen V2.1 (does not import builder)."""
import argparse,hashlib,json,re
from pathlib import Path
from .v21_audit import audit as audit_v21,require,AuditError
from .v2_audit import vector
ROOT=Path(__file__).resolve().parents[3]

def audit(directory):
 directory=Path(directory);p=directory/'m20v23_cpu_core.sv';text=p.read_text();net=json.loads(p.with_suffix('.netlist.json').read_text())
 base=ROOT/'rtl/m20/v21/generated/m20v21_cpu_core.sv';old=base.read_text();oldnet=json.loads(base.with_suffix('.netlist.json').read_text())
 a=audit_v21(base,base.with_suffix('.netlist.json'),base.parent.parent/'swc_mux157.sv')
 require(net['base_sv_sha256']==hashlib.sha256(old.encode()).hexdigest(),'base changed')
 require(net['source_sha256']==hashlib.sha256(text.encode()).hexdigest(),'V23 source hash mismatch')
 require(net['nodes']==oldnet['nodes'] and net['registers']==oldnet['registers'],'477 graph or33state mapping changed')
 require(text.count('swc_mux157_v23 #(')==477,'unexpected combinational count')
 boundary='    wire [32:0] state_q,state_qm,state_d;'
 require(text.count(boundary)==1,'state boundary missing');body,binding=text.split(boundary)
 body=body.split(');',1)[1];expected=old.split(');',1)[1].rsplit('endmodule',1)[0]
 for r in oldnet['registers']:
  declaration='logic '+(f'[{r["width"]-1}:0] ' if r['width']>1 else '')+r['name']+';'
  expected=expected.replace(declaration,declaration.replace('logic','wire',1))
  expected,n=re.subn(r'    always_ff @\(posedge clk\) begin\s*'+re.escape(r['name'])+r' <= [^;]+;\s*end','',expected)
  require(n==1,'base FF not recognized')
 body,n=re.subn(r'swc_mux157_v23 #\([^\n]*\) (u_n\d+) ',r'swc_mux157 \1 ',body)
 require(n==477 and re.sub(r'\s+','',body)==re.sub(r'\s+','',expected),'unaccounted combinational change')
 q=[v for r in oldnet['registers'] for v in r['qbits']];d=[v for r in oldnet['registers'] for v in r['dbits']]
 require(net['state_q_bits']==q and net['state_d_bits']==d,'flat mapping wrong')
 assignments=re.findall(r'assign ([\w\[\]]+)=state_q\[(\d+)\];',binding)
 require(assignments==[(v,str(i)) for i,v in enumerate(q)],'Q aliases changed')
 m=re.search(r'assign state_d=([^;]+);',binding);require(m is not None and vector(m[1])==d,'D alias changed')
 ideal,latches=binding.split('end else if(STATE_IMPL=="TWO_PHASE_LATCH") begin:g_latch')
 require(ideal.count('always_ff')==1 and 'logic [32:0] state_ff;' in ideal,'ideal boundary changed')
 m=re.search(r'always_ff @\(posedge clk\) state_ff <= ([^;]+);',ideal)
 require(m is not None and vector(m[1])==d,'ideal FFs not frozen D')
 require('always_ff' not in latches and 'always_latch' not in latches,'native state hidden in latch mode')
 cells=re.findall(r'b(\d+)\(\.master_hold\(master_hold\),\.slave_open\(slave_open\),\.d\(([^)]+)\),\.q\(state_q\[(\d+)\]\),\.qm\(state_qm\[(\d+)\]\),\.checks_enable\(checks_enable\)\);',latches)
 require(cells==[(str(i),v,str(i),str(i)) for i,v in enumerate(d)],'33 latch bit D/Q/QM mapping mismatch')
 model=(ROOT/'rtl/m20/v23/swc_ms_bit_v23.sv').read_text()
 require(len(re.findall(r'^ swc_mux157_v23 #',model,re.M))==2 and 'always_ff' not in model,'not exactly two feedback MUX per bit')
 require('.i0(d),.i1(qm),.y(qm)' in model and '.i0(q),.i1(qm),.y(q)' in model,'feedback mapping changed')
 # Reject hidden logic even if source/netlist hashes were refreshed together.
 require((net['physical_mux_count'],net['state_bits'],net['storage_mux'],net['total_full_interface'],net['functional_total'])==(477,33,66,543,542),'forged resource totals')
 remainder=binding
 for name,index in assignments:remainder=remainder.replace(f'    assign {name}=state_q[{index}];','',1)
 remainder=re.sub(r'    assign state_d=[^;]+;','',remainder,count=1)
 ideal_expected='generate if(STATE_IMPL=="IDEAL_FF") begin:g_ideal logic [32:0] state_ff; always_ff @(posedge clk) state_ff <= '+m[1]+'; assign state_q=state_ff;assign state_qm=state_ff;'
 # m currently refers to the independently checked IDEAL_FF D expression.
 norm=lambda value:re.sub(r'\s+','',value)
 normalized=norm(remainder)
 require(normalized.startswith(norm(ideal_expected)),'extra IDEAL_FF/binding logic')
 normalized=normalized[len(norm(ideal_expected)):]
 start='end else if(STATE_IMPL=="TWO_PHASE_LATCH") begin:g_latch'
 require(normalized.startswith(norm(start)),'latch branch changed');normalized=normalized[len(norm(start)):]
 for i,value in enumerate(d):
  cell=f'swc_ms_bit_v23 #(.DATA_NS(LATCH_DATA_NS),.SELECT_NS(LATCH_SELECT_NS),.MASTER_NS(MASTER_OFFSET_NS+{i%3}*BRANCH_SKEW_NS),.SLAVE_NS(SLAVE_OFFSET_NS+{(i+1)%3}*BRANCH_SKEW_NS),.CHECK_FATAL(CHECK_FATAL)) b{i}(.master_hold(master_hold),.slave_open(slave_open),.d({value}),.q(state_q[{i}]),.qm(state_qm[{i}]),.checks_enable(checks_enable));'
  require(normalized.startswith(norm(cell)),'opaque/changed latch implementation');normalized=normalized[len(norm(cell)):]
 require(normalized==norm('end else begin:g_bad initial $fatal(1,"unknown state implementation");end endgenerate endmodule `default_nettype wire'),'extra uncounted logic')
 result=dict(status='PASS',base_sha256=oldnet['source_sha256'],v23_sha256=net['source_sha256'],comb_mux=477,state_bits=33,
  ideal_ff_native_bits=33,two_phase_native_ff_bits=0,two_phase_storage_mux=66,full_equivalent=543,functional_equivalent=542,
  method='Frozen combinational body comparison + independent477/33 audit + exact D/Q/QM bit mappings; monitor counters excluded')
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,default=ROOT/'rtl/m20/v23/generated');p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=audit(a.input);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print('M20V23_AUDIT_PASS comb=477 storage=66')
