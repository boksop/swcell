`timescale 1ns/1ps
module tb_m20_v3_system #(
 parameter PONG_FILE="",SNAKE_FILE=""
);
 reg clk=0;always #10 clk=~clk;
 reg power_reset=1,reset_request=0,select_request=0,select_game=0;
 reg run_toggle=0,step_request=0,speed_request=0;reg[15:0] speed_ticks=50;reg[5:0] keys=0;
 wire game,active,run_requested,master_hold,slave_open,commit_ce,cpu_reset;
 wire input_sample_ce,input0_ack,input1_ack;wire[5:0] consumed_keys;
 wire[11:0] pc;wire[7:0] ar,ram_addr;wire[3:0] accumulator,gpo,ram_wdata,ram_rdata;
 wire z,c,halted,trapped,ram_ce,ram_oe,ram_we,retire_valid;
 wire[2:0] ustate;wire[15:0] instruction,phase,cycle_ticks;
 wire[63:0] microcycles,retired,reads,writes,ticks,errors,frame_ticks;
 wire[1023:0] frame_ram;wire frame_valid,frame_game,frame_pulse;wire[95:0] debug_sample;
 swc_m20_v3_system #(.PONG_FILE(PONG_FILE),.SNAKE_FILE(SNAKE_FILE),.PONG_HZ(100000),.SNAKE_HZ(100000)) dut(.*);
 wire[11:0] s_pc;wire[7:0] s_ar;wire[3:0] s_accumulator,s_gpo;wire s_z,s_c;wire[2:0] s_ustate;
 wire[1023:0] s_frame_ram;wire s_frame_pulse;wire[63:0] s_errors;
 swc_m20_v3_system #(.PONG_FILE(PONG_FILE),.SNAKE_FILE(SNAKE_FILE),.PONG_HZ(100000),.SNAKE_HZ(100000),.STORAGE_MODE("STRICT_MUX")) strict(
  .clk(clk),.power_reset(power_reset),.reset_request(reset_request),.select_request(select_request),.select_game(select_game),
  .run_toggle(run_toggle),.step_request(step_request),.speed_request(speed_request),.speed_ticks(speed_ticks),.keys(keys),
  .pc(s_pc),.ar(s_ar),.accumulator(s_accumulator),.gpo(s_gpo),.z(s_z),.c(s_c),.ustate(s_ustate),
  .frame_ram(s_frame_ram),.frame_pulse(s_frame_pulse),.errors(s_errors));
 integer csv,frame_csv,frames=0,commits=0;string outdir=".";
 integer clock_cycles=0,last_input_change=0;reg[26:0] last_inputs;
 always @(posedge clk)begin
  clock_cycles=clock_cycles+1;
  if({dut.held_keys,instruction,ram_rdata,cpu_reset}!==last_inputs)begin
   last_input_change=clock_cycles;last_inputs={dut.held_keys,instruction,ram_rdata,cpu_reset};
  end
  if(commit_ce&&!cpu_reset&&clock_cycles-last_input_change<8)$fatal(1,"V3_INPUT_SETTLE_BUDGET");
 end
 initial begin
  if($value$plusargs("OUT=%s",outdir))begin end
  csv=$fopen({outdir,"/system_trace.csv"},"w");
  frame_csv=$fopen({outdir,"/frame_snapshots.csv"},"w");
  $fwrite(frame_csv,"game,frame,ticks,ram_descending\n");
  $fwrite(csv,"game,micro,pc,word,a,ar,z,c,gpo,state,write_count,read_count,retire\n");
 end
 always @(posedge clk)if(commit_ce)begin
  #1;
  if({pc,ar,accumulator,z,c,gpo,ustate}!=={s_pc,s_ar,s_accumulator,s_z,s_c,s_gpo,s_ustate})
   $fatal(1,"V3_STRICT_FUNCTIONAL_STATE pc=%h strict=%h phase=%d",pc,s_pc,phase);
  commits=commits+1;
  $fwrite(csv,"%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n",game,microcycles,pc,instruction,accumulator,ar,z,c,gpo,ustate,writes,reads,retired);
 end
 always @(posedge frame_pulse)begin
  #1;
  if(!frame_valid||active||frame_ram!==s_frame_ram||!s_frame_pulse)$fatal(1,"V3_SNAPSHOT_MISMATCH");
  for(integer i=0;i<256;i=i+1)
   if(frame_ram[i*4+:4]!==dut.memory.memory[i])$fatal(1,"V3_TORN_SNAPSHOT %d",i);
  if(game)begin
   if(frame_ram[4*4+:4]<3||frame_ram[11*4+:4]>3)$fatal(1,"V3_SNAKE_STATE");
  end else if(frame_ram[4*0+:4]<1||frame_ram[4*0+:4]>14||frame_ram[4*1+:4]>7)$fatal(1,"V3_PONG_STATE");
  $writememh({outdir,game?"/snake_final.memh":"/pong_final.memh"},dut.memory.memory);
  frames=frames+1;
  $fwrite(frame_csv,"%d,%d,%d,%0256h\n",game,frames,ticks,frame_ram);
 end
 task pulse_reset;
  @(negedge clk);reset_request=1;@(negedge clk);reset_request=0;
 endtask
 task pulse_run;
  @(negedge clk);run_toggle=1;@(negedge clk);run_toggle=0;
 endtask
 reg[63:0] before_micro,before_writes;reg[32:0] before_state;
 initial begin
  repeat(5)@(negedge clk);power_reset=0;
  wait(frames>=64);
  pulse_run();wait(!active);repeat(300)@(negedge clk);
  before_micro=microcycles;before_writes=writes;before_state={pc,ar,accumulator,z,c,gpo,ustate};
  repeat(1000)@(negedge clk);
  if(microcycles!=before_micro||writes!=before_writes||before_state!=={pc,ar,accumulator,z,c,gpo,ustate})$fatal(1,"V3_STOP_CHANGED");
  if(debug_sample[6:0]!==7'b1000000)$fatal(1,"V3_STOP_STATUS_STALE %b",debug_sample[6:0]);
  @(negedge clk);step_request=1;@(negedge clk);step_request=0;
  wait(active);wait(!active);repeat(2)@(negedge clk);
  if(microcycles!=before_micro+1)$fatal(1,"V3_STEP_NOT_ONE");
  @(negedge clk);speed_request=1;speed_ticks=100;@(negedge clk);speed_request=0;
  if(cycle_ticks!=100)$fatal(1,"V3_SPEED_SAFE_CHANGE");
  pulse_reset();wait(cpu_reset);wait(!cpu_reset);wait(dut.warm_cycles==0&&!active);#1;
  if(ustate!=1||pc!=0||run_requested)$fatal(1,"V3_STOPPED_RESET_RELEASE");
  @(negedge clk);select_request=1;select_game=1;@(negedge clk);select_request=0;
  pulse_run();wait(game);wait(frame_game&&frame_valid);
  wait(frames>=128);
  // The original Snake IN1 bit1 path must perform the restart, not an FPGA RAM patch.
  keys=6'b100000;
  // Hold B until CPU boot itself reaches the init event, not merely one tick.
  do begin wait(!frame_pulse);wait(frame_pulse);#1;end while(frame_ram[14*4+:4]!=4);
  if(frame_ram[11*4+:4]!=0)$fatal(1,"V3_SNAKE_RESTART");
  @(negedge clk);keys=0;
  pulse_reset();wait(cpu_reset);wait(!cpu_reset);wait(frame_pulse);#1;
  if(errors!=0||s_errors!=0||frames<128)$fatal(1,"V3_ERROR_COUNTER F=%d S=%d frames=%d",errors,s_errors,frames);
  $fclose(csv);$fclose(frame_csv);$display("M20_V3_SYSTEM_PASS commits=%0d frames=%0d stop=1 step=1 reset=1 speed=1 strict_logic=1",commits,frames);$finish;
 end
 initial begin #500000000;$fatal(1,"V3_SYSTEM_TIMEOUT");end
endmodule
