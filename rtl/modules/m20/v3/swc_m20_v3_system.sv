`default_nettype none
// FPGA scheduling/peripherals only. The frozen MUX CPU makes every game decision.
module swc_m20_v3_system #(
 parameter integer CLK_HZ=50000000,PONG_HZ=10,SNAKE_HZ=5,
 parameter [11:0] PONG_TICK_DONE=m20_v3_game_pkg::PONG_DONE,SNAKE_TICK_DONE=m20_v3_game_pkg::SNAKE_DONE,
 parameter PONG_FILE="",SNAKE_FILE="",STORAGE_MODE="FUNCTIONAL_STORAGE"
)(input wire clk,power_reset,reset_request,select_request,select_game,
 input wire run_toggle,step_request,speed_request,input wire[15:0] speed_ticks,
 input wire[5:0] keys,
 output logic game=0,run_requested=1,active=0,
 output wire master_hold,slave_open,commit_ce,
 output wire input_sample_ce,input0_ack,input1_ack,
 output wire[5:0] consumed_keys,
 output wire[11:0] pc,output wire[7:0] ar,
 output wire[3:0] accumulator,gpo,output wire z,c,halted,trapped,
 output wire[2:0] ustate,output wire[15:0] instruction,
 output wire[7:0] ram_addr,output wire[3:0] ram_wdata,ram_rdata,
 output wire ram_ce,ram_oe,ram_we,retire_valid,
 output logic[63:0] microcycles=0,retired=0,reads=0,writes=0,ticks=0,errors=0,
 output logic[1023:0] frame_ram=0,output logic frame_valid=0,frame_game=0,
 output logic[63:0] frame_ticks=0,
 output logic frame_pulse=0,
 output wire[15:0] phase,cycle_ticks,
 output logic cpu_reset=1,
 output logic[95:0] debug_sample=0
);
 import m20_v3_game_pkg::*;
 localparam integer PONG_PERIOD=CLK_HZ/PONG_HZ,SNAKE_PERIOD=CLK_HZ/SNAKE_HZ;
 logic[15:0] phase_count=0,configured_ticks=50;
 logic[5:0] held_keys=0;
 logic[1:0] warm_cycles=3;
 logic reset_pending=0,desired_game=0,step_pending=0,stepping=0,park_pending=0,wait_tick=0;
 logic[31:0] tick_timer=0;
 logic[3:0] instruction_micro=0;
 logic held_retire=0,held_trap=0;logic[2:0] held_cost=0,held_state=0;
 logic held_in0=0,held_in1=0;
 logic[8:0] scan_index=0;logic scanning=0,snapshot_pending=0;
 logic[1023:0] scan_buffer=0;
 logic[63:0] scan_ticks=0;
 wire[3:0] view_data;
 wire write_commit,read_commit;
 assign phase=phase_count;assign cycle_ticks=configured_ticks;
 assign master_hold=!(active&&phase_count<20);
 assign slave_open=active&&phase_count>=25&&phase_count<40;
 assign commit_ce=active&&phase_count==25;
 assign input_sample_ce=active&&phase_count==0;
 assign consumed_keys=held_keys;
 assign input0_ack=commit_ce&&!cpu_reset&&held_retire&&held_in0;
 assign input1_ack=commit_ce&&!cpu_reset&&held_retire&&held_in1;
 wire rom_req=active&&phase_count==28;
 wire ram_req=active&&phase_count==4;
 wire write_ce=active&&phase_count==21;
 wire[11:0] rom_addr;
 wire trap_event;wire[2:0] retire_instruction_cycles;
 wire cpu_input_selected,cpu_input_bank;
 swc_m20_v3_memory #(.PONG_FILE(PONG_FILE),.SNAKE_FILE(SNAKE_FILE)) memory(
  .clk(clk),.cancel(cpu_reset),.game(game),.rom_req(rom_req),.rom_addr(rom_addr),.rom_data(instruction),
  .ram_req(ram_req),.write_ce(write_ce),.ram_addr(ram_addr),.ram_wdata(ram_wdata),
  .ram_ce(ram_ce),.ram_oe(ram_oe),.ram_we(ram_we),.ram_data(ram_rdata),
  .view_addr(scan_index[7:0]),.view_data(view_data),.write_commit(write_commit),.read_commit(read_commit));
 m20v3_cpu_core #(.STORAGE_MODE(STORAGE_MODE)) cpu(
  .clk(clk),.commit_ce(commit_ce),.master_hold(master_hold),.slave_open(slave_open),.rst(cpu_reset),
  .keys(held_keys),.rom_data(instruction),.ram_rdata(ram_rdata),
  .rom_addr(rom_addr),.ram_addr(ram_addr),.ram_wdata(ram_wdata),.ram_ce(ram_ce),.ram_oe(ram_oe),.ram_we(ram_we),
  .dbg_pc(pc),.dbg_ar(ar),.dbg_a(accumulator),.dbg_z(z),.dbg_c(c),.dbg_gpo(gpo),.dbg_state(ustate),
  .halted(halted),.trapped(trapped),.retire_valid(retire_valid),.trap_event(trap_event),.retire_instruction_cycles(retire_instruction_cycles),
  .debug_input_selected(cpu_input_selected),.debug_input_bank(cpu_input_bank));
 always_ff @(posedge clk)begin
  frame_pulse<=0;
  if(power_reset)begin
   game<=0;desired_game<=0;run_requested<=1;active<=0;phase_count<=0;configured_ticks<=50;
   cpu_reset<=1;held_keys<=0;warm_cycles<=3;reset_pending<=0;step_pending<=0;stepping<=0;
   park_pending<=0;wait_tick<=0;tick_timer<=0;instruction_micro<=0;
   microcycles<=0;retired<=0;reads<=0;writes<=0;ticks<=0;errors<=0;
   held_retire<=0;held_trap<=0;held_cost<=0;held_state<=0;held_in0<=0;held_in1<=0;scanning<=0;scan_index<=0;snapshot_pending<=0;
   scan_buffer<=0;frame_ram<=0;frame_valid<=0;frame_game<=0;frame_ticks<=0;scan_ticks<=0;debug_sample<=0;
  end else begin
   if(tick_timer!=0)tick_timer<=tick_timer-1'b1;
   if(run_toggle)run_requested<=!run_requested;
   if(step_request&&!run_requested)step_pending<=1;
   if(reset_request)reset_pending<=1;
   if(select_request)begin desired_game<=select_game;reset_pending<=1;end
   // The period change is consumed only while parked, never truncates a cycle.
   if(speed_request&&speed_ticks>=50&&!active)configured_ticks<=speed_ticks;
   if(write_commit)writes<=writes+1'b1;
   if(read_commit)reads<=reads+1'b1;
   if(scanning)begin
    if(scan_index>0&&scan_index<=256)scan_buffer[(scan_index-1)*4+:4]<=view_data;
    if(scan_index==257)begin
     frame_ram<=scan_buffer;frame_game<=game;frame_ticks<=scan_ticks;frame_valid<=1;frame_pulse<=1;scanning<=0;
    end else scan_index<=scan_index+1'b1;
   end
   if(!active)begin
    // The CPU/bus snapshot stays stable while parked, but controller status
    // must follow STOP/HALT/RESET instead of freezing at the last phase45.
    debug_sample[6:0]<={master_hold,slave_open,active,cpu_reset,run_requested,halted,trapped};
    if(reset_pending)begin
     reset_pending<=0;game<=desired_game;warm_cycles<=3;cpu_reset<=1;
     frame_valid<=0;scanning<=0;snapshot_pending<=0;wait_tick<=0;park_pending<=0;
     instruction_micro<=0;step_pending<=0;
    end else if(snapshot_pending&&!scanning)begin
     snapshot_pending<=0;scanning<=1;scan_index<=0;scan_ticks<=ticks;
    end else if(!scanning&&(warm_cycles!=0||step_pending||(run_requested&&(!wait_tick||tick_timer==0))))begin
     active<=1;phase_count<=0;stepping<=step_pending;step_pending<=0;park_pending<=0;
     if(wait_tick)begin wait_tick<=0;tick_timer<=game?32'(SNAKE_PERIOD-1):32'(PONG_PERIOD-1);end
    end
   end else begin
    // Two reset commits followed by a forced RESET->FETCH release cycle, even stopped.
    if(phase_count==0)begin held_keys<=keys;cpu_reset<=warm_cycles>1;end
    // Precommit signals are captured well before the FF CE, as in V23 PREVIEW.
    if(phase_count==19)begin
     held_retire<=retire_valid;held_trap<=trap_event;held_cost<=retire_instruction_cycles;held_state<=ustate;
     held_in0<=cpu_input_selected&&!cpu_input_bank;held_in1<=cpu_input_selected&&cpu_input_bank;
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
    // Sample after both the CPU CE and synchronous ROM response have settled.
    if(phase_count==45)begin
     debug_sample<={15'b0,pc,ar,accumulator,z,c,gpo,ustate,instruction,ram_addr,ram_wdata,ram_rdata,ram_ce,ram_oe,ram_we,held_keys,master_hold,slave_open,active,cpu_reset,run_requested,halted,trapped};
     if(!cpu_reset&&(halted||trapped))begin park_pending<=1;run_requested<=0;end
     if(!cpu_reset&&ustate==1&&pc==(game?SNAKE_TICK_DONE:PONG_TICK_DONE))begin
      park_pending<=1;wait_tick<=1;snapshot_pending<=1;ticks<=ticks+1'b1;
     end
    end
    if(phase_count==configured_ticks-1'b1)begin
     phase_count<=0;
     if(warm_cycles!=0)warm_cycles<=warm_cycles-1'b1;
     if(reset_pending||park_pending||!run_requested||stepping)begin active<=0;stepping<=0;end
    end else phase_count<=phase_count+1'b1;
   end
  end
 end
 // synthesis translate_off
 initial if(CLK_HZ<1||PONG_HZ<1||SNAKE_HZ<1)$fatal(1,"Invalid V3 rate");
 always @(posedge clk)if(!power_reset)begin
  if(!master_hold&&slave_open)$fatal(1,"V3_PHASE_OVERLAP");
  if(write_commit&&(cpu_reset||!active||phase_count!=21))$fatal(1,"V3_UNSAFE_WRITE");
 end
 // synthesis translate_on
endmodule
`default_nettype wire
