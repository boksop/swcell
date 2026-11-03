"""State-binding-only transform of frozen V2.1 SV; never regenerates its logic."""
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
PARAMS='''#(
 parameter string STATE_IMPL="TWO_PHASE_LATCH",
 parameter real COMB_DATA_MIN_NS=0.0,COMB_DATA_MAX_NS=0.0,
 parameter real COMB_SELECT_MIN_NS=0.0,COMB_SELECT_MAX_NS=0.0,
 parameter real LATCH_DATA_NS=0.0,LATCH_SELECT_NS=0.0,
 parameter real MASTER_OFFSET_NS=0.0,SLAVE_OFFSET_NS=0.0,
 parameter real BRANCH_SKEW_NS=0.0,
 parameter bit CHECK_FATAL=1
)'''

def generate(output):
 output=Path(output);output.mkdir(parents=True,exist_ok=True)
 base=ROOT/'rtl/m20/v21/generated/m20v21_cpu_core.sv';text=base.read_text()
 old=json.loads(base.with_suffix('.netlist.json').read_text());assert hashlib.sha256(text.encode()).hexdigest()==old['source_sha256']
 text=text.replace('module m20v21_cpu_core (','module m20v23_cpu_core '+PARAMS+' (\n    input wire master_hold,slave_open,checks_enable,')
 for r in old['registers']:
  width=r['width'];decl='logic '+(f'[{width-1}:0] ' if width>1 else '')+r['name']+';'
  assert decl in text;text=text.replace(decl,decl.replace('logic','wire',1))
  pattern=r'    always_ff @\(posedge clk\) begin\s*'+re.escape(r['name'])+r' <= [^;]+;\s*end'
  text,n=re.subn(pattern,'',text);assert n==1
 for n in old['nodes']:
  i=int(n['id'][1:]);factor=i%2
  params=f'#(.DATA_NS(COMB_DATA_MIN_NS+{factor}*(COMB_DATA_MAX_NS-COMB_DATA_MIN_NS)), .SELECT_NS(COMB_SELECT_MIN_NS+{factor}*(COMB_SELECT_MAX_NS-COMB_SELECT_MIN_NS)))'
  text=text.replace('swc_mux157 u_'+n['id']+' ', 'swc_mux157_v23 '+params+' u_'+n['id']+' ')
 qbits=[q for r in old['registers'] for q in r['qbits']];dbits=[d for r in old['registers'] for d in r['dbits']]
 binding=['    wire [32:0] state_q,state_qm,state_d;']
 for i,q in enumerate(qbits):binding.append(f'    assign {q}=state_q[{i}];')
 d='{'+','.join("1'b"+b if b in ('0','1') else b for b in reversed(dbits))+'}'
 binding.append(f'    assign state_d={d};')
 binding += ['    generate if(STATE_IMPL=="IDEAL_FF") begin:g_ideal',
             '      logic [32:0] state_ff;',f'      always_ff @(posedge clk) state_ff <= {d};',
             '      assign state_q=state_ff;assign state_qm=state_ff;',
             '    end else if(STATE_IMPL=="TWO_PHASE_LATCH") begin:g_latch']
 for i,d in enumerate(dbits):
  binding += [f'      swc_ms_bit_v23 #(.DATA_NS(LATCH_DATA_NS),.SELECT_NS(LATCH_SELECT_NS),',
              f'        .MASTER_NS(MASTER_OFFSET_NS+{i%3}*BRANCH_SKEW_NS),.SLAVE_NS(SLAVE_OFFSET_NS+{(i+1)%3}*BRANCH_SKEW_NS),.CHECK_FATAL(CHECK_FATAL))',
              f'        b{i}(.master_hold(master_hold),.slave_open(slave_open),.d({d}),.q(state_q[{i}]),.qm(state_qm[{i}]),.checks_enable(checks_enable));']
 binding += ['    end else begin:g_bad initial $fatal(1,"unknown state implementation");end endgenerate']
 text=text.replace('endmodule','\n'.join(binding)+'\nendmodule',1)
 (output/'m20v23_cpu_core.sv').write_text(text)
 manifest=dict(schema_version=1,module='m20v23_cpu_core',base_sv_sha256=old['source_sha256'],base_json_sha256=hashlib.sha256(base.with_suffix('.netlist.json').read_bytes()).hexdigest(),
  source_sha256=hashlib.sha256(text.encode()).hexdigest(),nodes=old['nodes'],registers=old['registers'],state_q_bits=qbits,state_d_bits=dbits,
  physical_mux_count=477,state_bits=33,storage_mux=66,total_full_interface=543,functional_total=542,
  note='Exactly frozen477 combinational instances; IDEAL_FF=33 nativeFF, TWO_PHASE_LATCH=66 feedback MUX. Checkers/scheduler/memory excluded.')
 (output/'m20v23_cpu_core.netlist.json').write_text(json.dumps(manifest,indent=2)+'\n');print('M20V23_GENERATED binding_only=1 comb=477 state=33 storage_mux=66')
 return manifest
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'rtl/m20/v23/generated');a=p.parse_args()
 for old in ('rtl/m20/v21','rtl/m20/v2','rtl/m20'):
  r=(ROOT/old).resolve();dest=a.output.resolve()
  if dest==r or (old!='rtl/m20' and r in dest.parents):p.error('refusing frozen baseline')
 generate(a.output)
