`timescale 1ns/1ps
module tb_m20v23_step;
 import m20_pkg::*;
 `include "v23_fixture.svh"
 integer i,steps=0;logic [32:0] saved;
 task one_step;
  begin
   @(negedge sys_clk);run_enable=0;stop_request=0;step_request=1;
   @(negedge sys_clk);step_request=0;
   wait(parked);#1;check_states();saved=dut.state_q;
   repeat(35)@(posedge sys_clk);
   if(saved!==dut.state_q || !master_hold || slave_open)$fatal(1,"CPU changed while stopped");
   steps=steps+1;
  end
 endtask
 initial begin
  for(i=0;i<4096;i=i+1)begin mem.bram.rom[i]=16'hffff;ref_mem.bram.rom[i]=16'hffff;ideal_mem.bram.rom[i]=16'hffff;switch_mem.bram.rom[i]=16'hffff;end
  for(i=0;i<256;i=i+1)begin mem.bram.memory[i]=0;ref_mem.bram.memory[i]=0;ideal_mem.bram.memory[i]=0;switch_mem.bram.memory[i]=0;end
  mem.bram.rom[0]=16'h0005;mem.bram.rom[1]=16'h8122;mem.bram.rom[2]=16'hf100;
  for(i=0;i<3;i=i+1)begin ref_mem.bram.rom[i]=mem.bram.rom[i];ideal_mem.bram.rom[i]=mem.bram.rom[i];switch_mem.bram.rom[i]=mem.bram.rom[i];end
  repeat(3)@(posedge sys_clk);@(negedge sys_clk);sched_reset=0;reset_all();prime();
  checks_enable=1;compare_enabled=1;
  repeat(9)one_step();
  if(dbg_state!==S_HALT || dbg_pc!==3 || dbg_a!==5 || mem.bram.memory[8'h22]!==5 || mem.write_count!=1)$fatal(1,"step result");
  repeat(3)one_step();if(mem.write_count!=1 || dbg_pc!==3)$fatal(1,"terminal step side effect");
  $display("M20V23_STEP_PASS microsteps=%0d writes=1 ordinary_cycles=2 memory_cycles=5 parked_state_stable=1",steps);$finish;
 end
 initial begin #100000;$fatal(1,"step watchdog");end
endmodule
