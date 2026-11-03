`timescale 1ns/1ps
module tb_m20v23_scheduler;
 logic sys_clk=0;always #10 sys_clk=~sys_clk;
 logic reset=1,run_enable=0,stop_request=0,step_request=0;
 wire master_hold,slave_open,commit_clk,commit_ce,rom_read_ce,ram_sample_ce,observe_ce,parked;
 wire [1:0] phase;integer phase_tick;
 integer commits=0,cycles=0,prior_phase=3,phase_length=0,stops=0;
 swc_two_phase_scheduler #(.MASTER_TICKS(12),.SLAVE_TICKS(10),.DEAD1_TICKS(3),.DEAD2_TICKS(5)) dut(.*);
 always @(posedge sys_clk)begin
  if(commit_ce)commits=commits+1;
  if(!parked)begin
   if(phase!=prior_phase)begin
    if(prior_phase==0 && phase_length!=12)$fatal(1,"master width");
    if(prior_phase==1 && phase_length!=3)$fatal(1,"dead1 width");
    if(prior_phase==2 && phase_length!=10)$fatal(1,"slave width");
    if(prior_phase==3 && phase_length!=0 && phase_length!=5)$fatal(1,"dead2 width");
    prior_phase=phase;phase_length=0;
   end
   phase_length=phase_length+1;
  end else begin prior_phase=3;phase_length=0;end
  #1ps;if(!master_hold && slave_open)$fatal(1,"scheduler overlap");
  if(parked && (!master_hold || slave_open))$fatal(1,"unsafe park");
 end
 task stop_at(input integer p);
  begin
   @(negedge sys_clk);run_enable=1;stop_request=0;
   wait(!parked && phase==p);@(negedge sys_clk);stop_request=1;
   wait(parked);@(negedge sys_clk);run_enable=0;stop_request=0;
   cycles=commits;repeat(40)@(posedge sys_clk);
   if(commits!=cycles)$fatal(1,"commit after stop");stops=stops+1;
  end
 endtask
 initial begin
  repeat(3)@(posedge sys_clk);@(negedge sys_clk);reset=0;
  repeat(5)begin
   cycles=commits;@(negedge sys_clk);step_request=1;@(negedge sys_clk);step_request=0;
   wait(!parked);wait(parked);repeat(4)@(posedge sys_clk);
   if(commits!=cycles+1)$fatal(1,"single step count");
  end
  stop_at(0);stop_at(1);stop_at(2);stop_at(3);
  $display("M20V23_SCHEDULER_PASS single_steps=5 stop_phases=%0d asymmetric_dead_ticks=3,5",stops);$finish;
 end
 initial begin #200000;$fatal(1,"scheduler watchdog");end
endmodule
