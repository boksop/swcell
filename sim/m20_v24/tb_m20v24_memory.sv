`timescale 1ns/1ps
module tb_m20v24_memory;
 import m20_pkg::*;
 `include "v24_fixture.svh"
 integer i,n,checks=0,retired,steps;
 task configure;
  begin
   for(i=0;i<4096;i=i+1)begin mem.bram.rom[i]=16'hffff;ref_mem.bram.rom[i]=16'hffff;ideal_mem.bram.rom[i]=16'hffff;switch_mem.bram.rom[i]=16'hffff;end
   mem.bram.rom[0]=16'h0005;mem.bram.rom[1]=16'h8122;mem.bram.rom[2]=16'h8022;mem.bram.rom[3]=16'he200;mem.bram.rom[4]=16'hf100;
   for(i=0;i<5;i=i+1)begin ref_mem.bram.rom[i]=mem.bram.rom[i];ideal_mem.bram.rom[i]=mem.bram.rom[i];switch_mem.bram.rom[i]=mem.bram.rom[i];end
   mem.rom_delay_ns=1.5;ref_mem.rom_delay_ns=1.5;ideal_mem.rom_delay_ns=1.5;switch_mem.rom_delay_ns=1.5;
   mem.ram_delay_ns=2;ref_mem.ram_delay_ns=2;ideal_mem.ram_delay_ns=2;switch_mem.ram_delay_ns=2;
  end
 endtask
 task until_state(input integer state_value);
  begin steps=0;while(dbg_state!=state_value)begin advance();steps=steps+1;if(steps>30)$fatal(1,"V23 memory state timeout");end end
 endtask
 task begin_program;
  begin reset_all();prime();compare_enabled=1;checks_enable=1;start();end
 endtask
 initial begin
  for(i=0;i<256;i=i+1)begin mem.bram.memory[i]=4'ha;ref_mem.bram.memory[i]=4'ha;ideal_mem.bram.memory[i]=4'ha;switch_mem.bram.memory[i]=4'ha;end
  repeat(3)@(posedge sys_clk);@(negedge sys_clk);sched_reset=0;configure();
  begin_program();until_state(S_MEM_ACCESS);
  @(posedge sys_clk);while(!ram_sample_ce)@(posedge sys_clk);#1ps;
  if(mem.pending_write!==1)$fatal(1,"ST snapshot missing");
  @(negedge sys_clk);rst=1;advance();park();
  if(mem.bram.memory[8'h22]!==4'ha || mem.write_count!=0)$fatal(1,"V23 pending reset wrote SRAM");checks=checks+1;
  begin_program();until_state(S_MEM_RELEASE);
  if(mem.bram.memory[8'h22]!==5 || mem.write_count!=1)$fatal(1,"V23 ACCESS write missing");
  rst=1;advance();park();if(mem.bram.memory[8'h22]!==5 || mem.write_count!=1)$fatal(1,"V23 reset rolled back write");checks=checks+1;
  begin_program();until_state(S_HALT);if(dbg_a!==5 || dbg_gpo!==5 || mem.write_count!=2)$fatal(1,"V23 SRAM/OUT/HALT");
  repeat(3)begin advance();if(retire_valid || ram_ce || ram_we)$fatal(1,"HALT repeated");end park();checks=checks+1;
  // Repeat the program without clearing RAM; registered two-edge reads remain in use.
  begin_program();until_state(S_HALT);if(mem.write_count!=3 || dbg_a!==5)$fatal(1,"V23 repeated registered SRAM");park();checks=checks+1;
  mem.bram.rom[0]=16'hffff;ref_mem.bram.rom[0]=16'hffff;ideal_mem.bram.rom[0]=16'hffff;switch_mem.bram.rom[0]=16'hffff;
  begin_program();until_state(S_TRAP);if(dbg_pc!==0 || dbg_a!==0 || mem.write_count!=3)$fatal(1,"V23 trap side effect");advance();park();checks=checks+1;
  reset_all();load_fixture(8,0,0,1,0,8);prime();compare_enabled=1;checks_enable=1;start();until_state(S_TRAP);
  if(dbg_pc!==8 || mem.write_count!=3)$fatal(1,"unloaded fill not real TRAP");park();checks=checks+1;
  mem.bram.rom[0]=16'hf100;ref_mem.bram.rom[0]=16'hf100;ideal_mem.bram.rom[0]=16'hf100;switch_mem.bram.rom[0]=16'hf100;
  begin_program();until_state(S_HALT);if(dbg_pc!==1 || dbg_gpo!==8 || mem.write_count!=3)$fatal(1,"TRAP reset recovery");park();checks=checks+1;
  for(i=0;i<256;i=i+1)begin
   if(mem.bram.memory[i]!==ref_mem.bram.memory[i] || mem.bram.memory[i]!==ideal_mem.bram.memory[i] || mem.bram.memory[i]!==switch_mem.bram.memory[i])$fatal(1,"memory model mismatch");
   if(i!=8'h22 && mem.bram.memory[i]!==4'ha)$fatal(1,"reset cleared SRAM");
  end
  $display("M20V24_MEMORY_PASS checks=%0d bram_rom_latency=2 bram_ram_latency=2 pending_write_abort=1 reset_no_rollback=1",checks);$finish;
 end
 initial begin #20000000;$fatal(1,"V23 memory watchdog");end
endmodule
