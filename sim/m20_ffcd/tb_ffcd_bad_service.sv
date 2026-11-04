`timescale 1ns/1ps
module tb_ffcd_bad_service;
 import m20_pkg::*;
 `include "ffcd_fixture.svh"
 integer i;
 initial begin
  for(i=0;i<4096;i=i+1)begin mem.bram.rom[i]=16'hffff;ref_mem.bram.rom[i]=16'hffff;ideal_mem.bram.rom[i]=16'hffff;switch_mem.bram.rom[i]=16'hffff;end
  for(i=0;i<256;i=i+1)begin mem.bram.memory[i]=4'ha;ref_mem.bram.memory[i]=4'ha;ideal_mem.bram.memory[i]=4'ha;switch_mem.bram.memory[i]=4'ha;end
  mem.bram.rom[0]=16'h0005;mem.bram.rom[1]=16'h8122;mem.bram.rom[2]=16'h8022;mem.bram.rom[3]=16'hf100;
  for(i=0;i<4;i=i+1)begin ref_mem.bram.rom[i]=mem.bram.rom[i];ideal_mem.bram.rom[i]=mem.bram.rom[i];switch_mem.bram.rom[i]=mem.bram.rom[i];end
  repeat(3)@(posedge sys_clk);@(negedge sys_clk);sched_reset=0;reset_all();prime();
 `ifdef FFCD_BAD_ROM
  mem.rom_delay_ns=300;ref_mem.rom_delay_ns=300;ideal_mem.rom_delay_ns=300;switch_mem.rom_delay_ns=300;
 `else
  mem.ram_delay_ns=500;ref_mem.ram_delay_ns=500;ideal_mem.ram_delay_ns=500;switch_mem.ram_delay_ns=500;
 `endif
  checks_enable=1;compare_enabled=1;start();repeat(30)advance();$fatal(1,"FFCD_BAD_SERVICE_NOT_DETECTED");
 end
 initial begin #100000;$fatal(1,"FFCD_BAD_SERVICE_WATCHDOG");end
endmodule
