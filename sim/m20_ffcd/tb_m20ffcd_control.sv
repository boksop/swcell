`timescale 1ns/1ps
module tb_m20ffcd_control;
 import m20_pkg::*;
 `include "ffcd_fixture.svh"
 integer i,steps=0,checks=0;
 logic[32:0] saved;logic[15:0]saved_rom;logic[3:0]saved_ram;
 task step_once;
  integer before_cycles;
  begin
   @(negedge sys_clk);stop_request=0;run_enable=0;
   wait(parked&&step_ready);before_cycles=microcycles;
   @(negedge sys_clk);run_enable=0;stop_request=0;step_request=1;
   @(negedge sys_clk);step_request=0;
   wait(!parked);wait(parked);#1;check_states();
   if(!step_ack)$fatal(1,"FFCD_STEP_ACK_MISSING");
   if(microcycles-before_cycles!=1)$fatal(1,"FFCD_STEP_NOT_ONE_MICROCYCLE %0d",microcycles-before_cycles);
   saved=dut.state_q;saved_rom=rom_data;saved_ram=ram_rdata;repeat(60)@(posedge sys_clk);#1;
   if(saved!==dut.state_q || !master_hold || slave_open || saved_rom!==rom_data || saved_ram!==ram_rdata)$fatal(1,"FFCD_STOPPED_STATE_CHANGED");
   steps=steps+1;
  end
 endtask
 initial begin
  for(i=0;i<4096;i=i+1)begin mem.bram.rom[i]=16'hffff;ref_mem.bram.rom[i]=16'hffff;ideal_mem.bram.rom[i]=16'hffff;switch_mem.bram.rom[i]=16'hffff;end
  for(i=0;i<256;i=i+1)begin mem.bram.memory[i]=0;ref_mem.bram.memory[i]=0;ideal_mem.bram.memory[i]=0;switch_mem.bram.memory[i]=0;end
  mem.bram.rom[0]=16'h0005;mem.bram.rom[1]=16'h8122;mem.bram.rom[2]=16'h8123;mem.bram.rom[3]=16'h8022;mem.bram.rom[4]=16'hf100;
  for(i=0;i<5;i=i+1)begin ref_mem.bram.rom[i]=mem.bram.rom[i];ideal_mem.bram.rom[i]=mem.bram.rom[i];switch_mem.bram.rom[i]=mem.bram.rom[i];end
  repeat(3)@(posedge sys_clk);@(negedge sys_clk);sched_reset=0;reset_all();prime();checks_enable=1;compare_enabled=1;
  // STOP dominates a simultaneous STEP; no accepted microcycle.
  saved=dut.state_q;@(negedge sys_clk);step_request=1;stop_request=1;
  @(negedge sys_clk);step_request=0;repeat(70)@(posedge sys_clk);#1;
  if(!parked || saved!==dut.state_q)$fatal(1,"FFCD_STOP_STEP_PRIORITY");stop_request=0;checks=checks+1;
  // LDI2 + STORE5 + STORE5 + LOAD5 + HALT2 =19 unchanged microcycles.
  repeat(19)step_once();
  if(dbg_state!==S_HALT || dbg_pc!==5 || dbg_a!==5 || mem.write_count!=2 || mem.bram.memory[8'h22]!==5 || mem.bram.memory[8'h23]!==5)$fatal(1,"FFCD_STEPPED_MEMORY");checks=checks+1;
  repeat(3)step_once();if(mem.write_count!=2)$fatal(1,"FFCD_TERMINAL_REPEAT_WRITE");checks=checks+1;
  // RESET ignores STEP; reset itself still requires actual RUN initialization.
  compare_enabled=0;checks_enable=0;rst=1;@(negedge sys_clk);step_request=1;
  @(negedge sys_clk);step_request=0;repeat(70)@(posedge sys_clk);#1;
  if(!parked)$fatal(1,"FFCD_RESET_ACCEPTED_STEP");checks=checks+1;
  reset_all();prime();checks_enable=1;compare_enabled=1;step_once();
  start();repeat(5)advance();@(negedge sys_clk);run_enable=0;stop_request=1;step_request=1;
  wait(parked);@(negedge sys_clk);step_request=0;saved=dut.state_q;repeat(70)@(posedge sys_clk);#1;
  if(saved!==dut.state_q || mem.pending_write)$fatal(1,"FFCD_RUN_STOP_DRAIN");checks=checks+1;
  // Continue RUN after STOP to terminal, then exercise TRAP stepping.
  start();while(!halted)advance();park();if(mem.write_count!=4)$fatal(1,"FFCD_RESUME_WRITE_COUNT");checks=checks+1;
  compare_enabled=0;checks_enable=0;mem.bram.rom[0]=16'hffff;ref_mem.bram.rom[0]=16'hffff;ideal_mem.bram.rom[0]=16'hffff;switch_mem.bram.rom[0]=16'hffff;
  reset_all();prime();checks_enable=1;compare_enabled=1;repeat(2)step_once();
  if(!trapped)$fatal(1,"FFCD_TRAP_STEP");step_once();if(mem.write_count!=4)$fatal(1,"FFCD_TRAP_WRITE");checks=checks+1;
  $display("M20FFCD_CONTROL_PASS checks=%0d explicit_steps=%0d stop_step_priority=1 reset_step_ignored=1 writes_single=1",checks,steps);$finish;
 end
 initial begin #2000000;$fatal(1,"FFCD_CONTROL_WATCHDOG");end
endmodule
