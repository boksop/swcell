`default_nettype none
// V3 timing windows retained. Continuous CPU execution, debug-only parking.
module swc_m20_v31_service #(
 parameter ROM_FILE="",parameter integer CYCLE_TICKS=50
)(input wire clk,power_reset,start_enable,reset_request,run_toggle,step_request,
 input wire[5:0] keys,
 output logic active=0,run_requested=1,cpu_reset=1,
 output wire master_hold,slave_open,commit_ce,
 output wire[11:0] pc,output wire[7:0] ar,ram_addr,
 output wire[3:0] accumulator,gpo,ram_wdata,ram_rdata,
 output wire z,c,halted,trapped,ram_ce,ram_oe,ram_we,retire_valid,
 output wire[2:0] ustate,output wire[15:0] instruction,
 output logic[15:0] phase=0,
 output logic[63:0] microcycles=0,retired=0,reads=0,writes=0,errors=0,
 output wire write_commit,read_commit,
 output logic held_retire=0,output logic[15:0] held_word=0,
 output logic[11:0] held_pc=0
);
 wire[5:0] held_keys=keys; // Alias only: continuous synchronized levels, no event/sample storage.
 logic[1:0] warm_cycles=3;
 logic reset_pending=0,step_pending=0,stepping=0,park_pending=0;
 logic[3:0] instruction_micro=0;
 logic held_trap=0;logic[2:0] held_cost=0,held_state=0;
 wire[11:0] rom_addr;wire trap_event;wire[2:0] retire_instruction_cycles;
 assign master_hold=!(active&&phase<20);
 assign slave_open=active&&phase>=25&&phase<40;
 assign commit_ce=active&&phase==25;
 swc_m20_v31_memory #(.ROM_FILE(ROM_FILE)) memory(
  .clk(clk),.cancel(cpu_reset),.rom_req(active&&phase==28),.rom_addr(rom_addr),.rom_data(instruction),
  .ram_req(active&&phase==4),.write_ce(active&&phase==21),.ram_addr(ram_addr),.ram_wdata(ram_wdata),
  .ram_ce(ram_ce),.ram_oe(ram_oe),.ram_we(ram_we),.ram_data(ram_rdata),
  .write_commit(write_commit),.read_commit(read_commit));
 m20v3_cpu_core #(.STORAGE_MODE("FUNCTIONAL_STORAGE")) cpu(
  .clk(clk),.commit_ce(commit_ce),.master_hold(master_hold),.slave_open(slave_open),.rst(cpu_reset),
  .keys(held_keys),.rom_data(instruction),.ram_rdata(ram_rdata),
  .rom_addr(rom_addr),.ram_addr(ram_addr),.ram_wdata(ram_wdata),.ram_ce(ram_ce),.ram_oe(ram_oe),.ram_we(ram_we),
  .dbg_pc(pc),.dbg_ar(ar),.dbg_a(accumulator),.dbg_z(z),.dbg_c(c),.dbg_gpo(gpo),.dbg_state(ustate),
  .halted(halted),.trapped(trapped),.retire_valid(retire_valid),.trap_event(trap_event),
  .retire_instruction_cycles(retire_instruction_cycles),.debug_input_selected(),.debug_input_bank());
 always_ff @(posedge clk)begin
  if(power_reset)begin
   active<=0;run_requested<=1;cpu_reset<=1;phase<=0;warm_cycles<=3;
   reset_pending<=0;step_pending<=0;stepping<=0;park_pending<=0;instruction_micro<=0;
   microcycles<=0;retired<=0;reads<=0;writes<=0;errors<=0;
   held_retire<=0;held_trap<=0;held_cost<=0;held_state<=0;held_pc<=0;held_word<=0;
  end else begin
   if(run_toggle)run_requested<=!run_requested;
   if(step_request&&!run_requested)step_pending<=1;
   if(reset_request)reset_pending<=1;
   if(write_commit)writes<=writes+1'b1;
   if(read_commit)reads<=reads+1'b1;
   if(!active)begin
    if(reset_pending)begin
     reset_pending<=0;warm_cycles<=3;cpu_reset<=1;
     instruction_micro<=0;step_pending<=0;park_pending<=0;
    end else if(warm_cycles!=0||(start_enable&&(step_pending||run_requested)))begin
     active<=1;phase<=0;stepping<=step_pending;step_pending<=0;park_pending<=0;
    end
   end else begin
    if(phase==0)cpu_reset<=warm_cycles>1;
    if(phase==19)begin
     held_retire<=retire_valid;held_trap<=trap_event;held_cost<=retire_instruction_cycles;
     held_state<=ustate;held_pc<=pc;held_word<=instruction;
    end
    if(commit_ce)begin
     if(!cpu_reset)begin
      microcycles<=microcycles+1'b1;
      if(held_state==0)instruction_micro<=0;
      else if(held_retire)begin
       retired<=retired+1'b1;
       if(instruction_micro+1'b1!={1'b0,held_cost})errors<=errors+1'b1;
       instruction_micro<=0;
      end else if(held_trap||held_state>=6)instruction_micro<=0;
      else instruction_micro<=instruction_micro+1'b1;
     end else instruction_micro<=0;
    end
    if(phase==45&&!cpu_reset&&(halted||trapped))begin park_pending<=1;run_requested<=0;end
    if(phase==CYCLE_TICKS-1)begin
     phase<=0;
     if(warm_cycles!=0)warm_cycles<=warm_cycles-1'b1;
     if(reset_pending||park_pending||!run_requested||stepping||(!start_enable&&warm_cycles<=1))begin active<=0;stepping<=0;end
    end else phase<=phase+1'b1;
   end
  end
 end
 // synthesis translate_off
 initial if(CYCLE_TICKS<50||CYCLE_TICKS>65535)$fatal(1,"V31_BAD_PERIOD");
 always @(posedge clk)if(!power_reset)begin
  if(!master_hold&&slave_open)$fatal(1,"V31_PHASE_OVERLAP");
  if(write_commit&&(cpu_reset||!active||phase!=21))$fatal(1,"V31_UNSAFE_WRITE");
 end
 // synthesis translate_on
endmodule
`default_nettype wire
