`timescale 1ns/1ps
module tb_m20v23_illegal;
 import m20_pkg::*;
 `include "v23_fixture.svh"
 integer w,i,checked=0,legal_count=0;
 logic [32:0] held;
 function automatic bit legal_word(input logic [15:0] v);
  case(v[15:12])
   0,1,2,3,4,5,6:legal_word=(v[11:4]==0);
   7:legal_word=(v==16'h7000 || v==16'h7100 || v==16'h7200);
   8:legal_word=(v[11:8]<=9);
   9:legal_word=(v[11:8]<=9 && v[7:0]==0);
   10:legal_word=((v&16'hfff0)==16'ha000 || (v&16'hfff0)==16'ha100 || (v>=16'ha200 && v<=16'ha600 && v[7:0]==0));
   11,12,13:legal_word=1;
   14:legal_word=(v==16'he000 || v==16'he100 || v==16'he200);
   15:legal_word=(v==16'hf000 || v==16'hf100);
   default:legal_word=0;
  endcase
 endfunction
 initial begin
  for(i=0;i<256;i=i+1)begin mem.bram.memory[i]=4'ha;ref_mem.bram.memory[i]=4'ha;ideal_mem.bram.memory[i]=4'ha;switch_mem.bram.memory[i]=4'ha;end
  repeat(3)@(posedge sys_clk);@(negedge sys_clk);sched_reset=0;
  for(w=0;w<65536;w=w+1)begin
   if(legal_word(w[15:0]))legal_count=legal_count+1;
   else begin
    checks_enable=0;compare_enabled=0;park();
    mem.bram.rom[0]=w[15:0];ref_mem.bram.rom[0]=w[15:0];ideal_mem.bram.rom[0]=w[15:0];switch_mem.bram.rom[0]=w[15:0];
    reset_all();load_fixture(0,9,8'h45,0,1,6);held=dut.state_q;
    compare_enabled=1;checks_enable=1;start();advance();
    if(dbg_state!==2 || trap_event!==1 || retire_valid!==0 || debug_next_state!==7)$fatal(1,"V23 illegal EXEC word=%h",w);
    advance();
    if(dbg_state!==7 || dut.state_q[29:0]!==held[29:0] || ram_we || ram_ce || retire_valid)$fatal(1,"V23 illegal actual terminal word=%h",w);
    advance();if(dbg_state!==7 || retire_valid || ram_we)$fatal(1,"TRAP not held");park();
    // Actual reset and NOP execution recover the feedback-latch CPU for every word.
    checks_enable=0;compare_enabled=0;mem.bram.rom[0]=16'hf000;ref_mem.bram.rom[0]=16'hf000;ideal_mem.bram.rom[0]=16'hf000;switch_mem.bram.rom[0]=16'hf000;
    reset_all();prime();checks_enable=1;compare_enabled=1;start();advance();advance();
    if(dbg_pc!==1 || dbg_state!==1)$fatal(1,"V23 illegal recovery word=%h",w);park();checked=checked+1;
   end
  end
  if(checked!=50521 || legal_count!=15015)$fatal(1,"illegal coverage count");
  if(mem.write_count!=0 || ref_mem.write_count!=0 || ideal_mem.write_count!=0 || switch_mem.write_count!=0)$fatal(1,"illegal SRAM write side effect");
  $display("M20V23_ILLEGAL_PASS words=65536 legal=15015 illegal=50521 actual_trap=50521 recovered=50521");$finish;
 end
 initial begin #2000000000;$fatal(1,"V23 illegal watchdog");end
endmodule
