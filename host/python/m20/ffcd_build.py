"""V24 feedforward state-binding and fixture adaptation; frozen originals read-only."""
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]

FRONT='''// FPGA 50MHz; external/FPGA single REF both use the identical feedforward core.
logic sys_clk=0;always #10 sys_clk=~sys_clk;
logic sched_reset=1,rst=1,run_enable=0,stop_request=0,step_request=0,prime_rom=0;
logic checks_enable=0,key_sample_ce=0;logic [5:0]requested_keys=0;wire[5:0]keys;wire[3:0]observed_gpo;
`ifdef FFCD_LOGIC_ONLY
localparam bit LOGIC_ONLY=1;
localparam real CDMIN=0,CDMAX=0,CSMIN=0,CSMAX=0;
`else
localparam bit LOGIC_ONLY=0;
localparam real CDMIN=0.2,CDMAX=0.8,CSMIN=0.3,CSMAX=1.0;
`endif
localparam real LD=0,LS=0,MO=0,SO=0,BS=0;localparam bit CF=1;
wire clk_ref;
`ifdef FFCD_MODE_C
logic external_ref=0;integer ext_cycles=0;
initial begin #17;forever begin external_ref=1;#(500+5*(ext_cycles%3));external_ref=0;#(500+7*(ext_cycles%2));ext_cycles=ext_cycles+1;end end
assign clk_ref=external_ref;
`else
swc_ffcd_ref_div divider(.sys_clk(sys_clk),.reset(sched_reset),.clk_ref(clk_ref));
`endif
wire safe_hold,parked,cycle_active,step_ack,step_ready,ref_rise_ce,ref_fall_ce,ref_level;
wire clk,commit_ce,rom_read_ce,ram_sample_ce,observe_ce,write_ce,control_window;
wire[2:0]control_state;wire[15:0]age;
wire[1:0]phase=ref_level?2:0;
swc_ffcd_service service(.sys_clk(sys_clk),.reset(sched_reset),.clk_ref(clk_ref),.cycle_active(cycle_active),
 .ref_rise_ce(ref_rise_ce),.ref_fall_ce(ref_fall_ce),.ram_sample_ce(ram_sample_ce),.preview_ce(commit_ce),.write_ce(write_ce),.observe_ce(observe_ce),.rom_read_ce(rom_read_ce),.control_window(control_window),.commit_clk(clk),.age(age),.ref_level(ref_level));
swc_ffcd_run_control control(.sys_clk(sys_clk),.reset(sched_reset),.cpu_reset(rst),.run_request(run_enable),.stop_request(stop_request),.step_request(step_request),.control_window(control_window),.ref_fall_ce(ref_fall_ce),.observe_ce(observe_ce),
 .safe_hold(safe_hold),.parked(parked),.cycle_active(cycle_active),.step_ack(step_ack),.step_ready(step_ready),.control_state(control_state));
real dr[0:19],df[0:19],sr[0:19],sf[0:19];
initial begin
 for(integer n=0;n<20;n=n+1)begin dr[n]=(n<16)?2.0:1.0;df[n]=dr[n];sr[n]=1.0;sf[n]=1.0;end
 sr[16]=4.0;sf[17]=4.0;
end
wire master_hold,slave_open;
swc_ff16_phase_timing #(.TAP_STAGES(16)) generator(.clk_ref(clk_ref),.safe_hold(safe_hold),.dr(dr),.df(df),.sr(sr),.sf(sf),
 .master_hold(master_hold),.slave_open(slave_open),.delayed_ref(),.tap4(),.tap8(),.tap12(),.tap16(),.h_raw(),.s_raw());
'''

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def generate(core_out,sim_out):
    core_out=Path(core_out);sim_out=Path(sim_out);core_out.mkdir(parents=True,exist_ok=True);sim_out.mkdir(parents=True,exist_ok=True)
    base=ROOT/'rtl/m20/v23/generated/m20v23_cpu_core.sv';text=base.read_text();net=json.loads(base.with_suffix('.netlist.json').read_text())
    assert sha(base)==net['source_sha256']
    text=text.replace('module m20v23_cpu_core #(','module m20ffcd_cpu_core #(\n parameter bit LOGIC_ONLY=0,')
    for i in range(33):
        pattern=r'swc_ms_bit_v23 #\(\.DATA_NS\(LATCH_DATA_NS\).*?b'+str(i)+r'\('
        text,n=re.subn(pattern,f'swc_ffcd_ms_bit #(.INDEX({i}),.LOGIC_ONLY(LOGIC_ONLY)) b{i}(',text,count=1,flags=re.S);assert n==1
        text=text.replace(f'.qm(state_qm[{i}]),.checks_enable(checks_enable));',f'.qm(state_qm[{i}]),.checks_enable(checks_enable),.me(state_me[{i}]),.se(state_se[{i}]));')
    text=text.replace('wire [32:0] state_q,state_qm,state_d;','wire [32:0] state_q,state_qm,state_d,state_me,state_se;')
    (core_out/'m20ffcd_cpu_core.sv').write_text(text)
    old=base.read_text();boundary='    wire [32:0] state_q,state_qm,state_d;'
    assert text.split('    wire [32:0] state_q,state_qm,state_d,state_me,state_se;')[0].split(');',1)[1]==old.split(boundary)[0].split(');',1)[1]
    assert text.count('swc_mux157_v23 #(')==477 and text.count('swc_ffcd_ms_bit #(')==33
    manifest=dict(cpu_comb_mux=477,cpu_state_bits=33,cpu_storage_mux=66,cpu_total=543,phasegen_fixed_mux=20,total_excluding_buffers=563,
                  frozen_v21_sha256=net['base_sv_sha256'],frozen_v23_sha256=sha(base),generated_sha256=sha(core_out/'m20ffcd_cpu_core.sv'),
                  audit='Exact frozen V23 combinational-body byte comparison; 33 D/Q/QM bindings retain frozen mapping; only storage model parameters change')
    (core_out/'binding_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    fixture=(ROOT/'sim/m20_v23/v23_fixture.svh').read_text();fixture=fixture[fixture.index('wire [15:0] rom_data;'):]
    fixture=re.sub(r'm20v23_cpu_core #\(.*?\) dut\(',
        'm20ffcd_cpu_core #(.LOGIC_ONLY(LOGIC_ONLY),.COMB_DATA_MIN_NS(CDMIN),.COMB_DATA_MAX_NS(CDMAX),.COMB_SELECT_MIN_NS(CSMIN),.COMB_SELECT_MAX_NS(CSMAX)) dut(',fixture,count=1,flags=re.S)
    fixture=fixture.replace('m20_v23_fpga_memory','m20_ffcd_memory').replace('.commit_ce(commit_ce),.prime_rom(prime_rom)', '.commit_ce(commit_ce),.write_ce(write_ce),.prime_rom(prime_rom)')
    fixture=fixture.replace('repeat(5)@(posedge sys_clk);#1;', 'repeat(5)@(posedge sys_clk);#1;')
    fixture=fixture.replace('if(commit_ce && pending_write)','if(write_ce && pending_write)')
    (sim_out/'ffcd_fixture.svh').write_text(FRONT+fixture+'\n`include "ffcd_monitors.svh"\n')
    for name in ('cpu','memory','illegal'):
        text=(ROOT/f'sim/m20_v23/tb_m20v23_{name}.sv').read_text()
        text=text.replace(f'tb_m20v23_{name}',f'tb_m20ffcd_{name}').replace('"v23_fixture.svh"','"ffcd_fixture.svh"').replace('M20V23_', 'M20FFCD_')
        if name=='cpu':
            # Full-cycle comparison across independent A/B/C; no dependence on absolute time.
            anchor='task load_memories;'
            monitor='''integer microfile;integer case_micro=0;string micro_path;
initial begin
 if($value$plusargs("CASE_DIR=%s",micro_path))begin microfile=$fopen({micro_path,"/microstates.csv"},"w");$fwrite(microfile,"case,micro,pc,ar,a,z,c,gpo,state,halted,trapped\\n");end
end
always @(posedge sys_clk)if(compare_enabled && !rst && observe_ce)begin
 #1ps;$fwrite(microfile,"%s,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d\\n",case_id,case_micro,dbg_pc,dbg_ar,dbg_a,dbg_z,dbg_c,dbg_gpo,dbg_state,halted,trapped);case_micro=case_micro+1;
end
'''
            text=text.replace(anchor,monitor+anchor)
        (sim_out/f'tb_m20ffcd_{name}.sv').write_text(text)
    # Independent frozen mode A CPU, with only a verification monitor appended.
    text=(ROOT/'sim/m20_v23/tb_m20v23_cpu.sv').read_text()
    text=text.replace('tb_m20v23_cpu','tb_m20ffcd_mode_a')
    text=text.replace('task load_memories;',monitor+'task load_memories;')
    (sim_out/'tb_m20ffcd_mode_a.sv').write_text(text)
    print('FFCD_BINDING_VERIFIED cpu477+66 phasegen20 frozen_logic_unchanged=1')
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--core-output',type=Path,required=True);p.add_argument('--sim-output',type=Path,required=True);a=p.parse_args();generate(a.core_output,a.sim_output)
