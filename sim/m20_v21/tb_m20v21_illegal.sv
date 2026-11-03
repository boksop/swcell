`timescale 1ns/1ps
module tb_m20v21_illegal;
 import m20_pkg::*;
 `include "m20v21_tb_fixture.svh"
 integer w,legal_count=0,illegal_count=0,recovered=0,j;
 task reset_both;
  begin
   @(negedge clk);rst=1;
   @(posedge clk);#1ps;
   if({dbg_pc,dbg_ar,dbg_a,dbg_z,dbg_c,dbg_gpo,dbg_state}!=={12'd0,8'd0,4'd0,1'b1,1'b0,4'd8,3'd0})
     $fatal(1,"reset recovery wrong");
  end
 endtask
 initial begin
  rom.read_delay_ps=0;ref_rom.read_delay_ps=0;
  rom.valid_words=4096;ref_rom.valid_words=4096;
  ram.mode=0;ref_ram.mode=0;ram.read_delay_ps=0;ref_ram.read_delay_ps=0;
  for(j=0;j<256;j=j+1)begin ram.memory[j]=j[3:0];ref_ram.memory[j]=j[3:0];end
  for(w=0;w<65536;w=w+1) begin
   lockstep_enabled=0;
   reset_both();
   rom.memory[0]=w[15:0];ref_rom.memory[0]=w[15:0];
   rom.memory[12'h123]=w[15:0];ref_rom.memory[12'h123]=w[15:0];
   rom.configuration_changed=~rom.configuration_changed;ref_rom.configuration_changed=~ref_rom.configuration_changed;
   #1;
   if(debug_legal!==legal_word(w[15:0]))$fatal(1,"legality word=%h",w);
   if(legal_word(w[15:0]))legal_count=legal_count+1;
   else begin
    illegal_count=illegal_count+1;
    @(negedge clk);rst=0;
    @(posedge clk);#1ps;if(dbg_state!==1)$fatal(1,"no FETCH");
    @(negedge clk);
    dut.pc_reg=12'h123;ref_dut.u_pc.value=12'h123;
    dut.ar_reg=8'h45;ref_dut.u_ar.value=8'h45;
    dut.a_reg=9;ref_dut.a_reg=9;dut.z_reg=0;ref_dut.z_reg=0;dut.c_reg=1;ref_dut.c_reg=1;
    dut.gpo_reg=6;ref_dut.gpo_reg=6;lockstep_enabled=1;
    @(posedge clk);#1;
    if(dbg_state!==2 || trap_event!==1 || retire_valid!==0 || debug_next_state!==7 || ram_we!==0 || ram_ce!==0)
      $fatal(1,"illegal EXEC word=%h state=%h next=%h",w,dbg_state,debug_next_state);
    repeat(3)begin
     @(posedge clk);#1;
     if({dbg_pc,dbg_ar,dbg_a,dbg_z,dbg_c,dbg_gpo,dbg_state}!=={12'h123,8'h45,4'd9,1'b0,1'b1,4'd6,3'd7})
       $fatal(1,"illegal committed wrong word=%h state=%h",w,dbg_state);
     if(retire_valid!==0 || ram_we!==0 || ram_ce!==0 || ram_oe!==0)$fatal(1,"TRAP side effect");
    end
    reset_both();
    rom.memory[0]=16'hF000;ref_rom.memory[0]=16'hF000;
    rom.configuration_changed=~rom.configuration_changed;ref_rom.configuration_changed=~ref_rom.configuration_changed;
    @(negedge clk);rst=0;
    repeat(3)begin @(posedge clk);#1;end
    if(dbg_pc!==1 || dbg_state!==1)$fatal(1,"TRAP reset failed to execute NOP word=%h",w);
    recovered=recovered+1;
   end
  end
  if(legal_count!=15015 || illegal_count!=50521 || recovered!=50521)$fatal(1,"coverage totals");
  $display("M20V21_ILLEGAL_PASS words=65536 legal=15015 illegal=50521 recovery=50521");$finish;
 end
 initial begin #20000000;$fatal(1,"illegal exhaustive watchdog");end
endmodule
