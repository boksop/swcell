`timescale 1ns/1ps
`define M20V21_MANUAL_CLOCK
module tb_m20v21_datapath;
 import m20_pkg::*;
 `include "m20v21_tb_fixture.svh"
 integer major,sub,ai,bi,ci,zi,w,operation,value,ea,ez,ec,checks=0,xchecks=0;
 task bind_state(input integer word,input integer av,input integer bv,input integer cv,input integer zv,input integer st);
  begin
   clk=0;rst=0;
   dut.pc_reg=0;ref_dut.u_pc.value=0;dut.ar_reg=8'h25;ref_dut.u_ar.value=8'h25;
   dut.a_reg=av[3:0];ref_dut.a_reg=av[3:0];dut.z_reg=zv[0];ref_dut.z_reg=zv[0];dut.c_reg=cv[0];ref_dut.c_reg=cv[0];
   dut.gpo_reg=8;ref_dut.gpo_reg=8;dut.state_reg=st[2:0];ref_dut.u_control.state_reg=st[2:0];
   rom.memory[0]=word[15:0];ref_rom.memory[0]=word[15:0];
   ram.memory[8'h25]=bv[3:0];ref_ram.memory[8'h25]=bv[3:0];
   rom.configuration_changed=~rom.configuration_changed;ref_rom.configuration_changed=~ref_rom.configuration_changed;
   ram.configuration_changed=~ram.configuration_changed;ref_ram.configuration_changed=~ref_ram.configuration_changed;
   #1;
  end
 endtask
 task step_check;
  begin
   if(debug_legal!==1 || retire_valid!==1)$fatal(1,"datapath not committing %h",w);
   clk=1;#1;
   if({dbg_a,dbg_z,dbg_c}!=={ea[3:0],ez[0],ec[0]})
    $fatal(1,"math word=%h a=%d b=%d c=%d z=%d got=%h/%b/%b expected=%h/%b/%b",w,ai,bi,ci,zi,dbg_a,dbg_z,dbg_c,ea[3:0],ez[0],ec[0]);
   clk=0;checks=checks+1;
  end
 endtask
 initial begin
  rom.read_delay_ps=0;ref_rom.read_delay_ps=0;rom.valid_words=4096;ref_rom.valid_words=4096;
  ram.mode=0;ref_ram.mode=0;ram.read_delay_ps=0;ref_ram.read_delay_ps=0;
  lockstep_enabled=1;
  for(major=0;major<=9;major=major+1)if(major<=6 || major>=8)
   for(sub=0;sub<(major>=8?10:1);sub=sub+1)
    for(ai=0;ai<16;ai=ai+1)for(bi=0;bi<16;bi=bi+1)for(ci=0;ci<2;ci=ci+1)for(zi=0;zi<2;zi=zi+1)begin
     w=major<8?((major<<12)|bi):((major<<12)|(sub<<8)|(major==8?8'h25:0));
     if(major<8)case(major)0:operation=0;1:operation=2;2:operation=3;3:operation=4;4:operation=5;5:operation=7;6:operation=8;endcase
     else operation=sub;
     ea=ai;ez=zi;ec=ci;
     case(operation)
      0:begin ea=bi;ez=(ea==0);end
      2,3:begin value=ai+bi+(operation==3?ci:0);ea=value&15;ez=(ea==0);ec=(value>=16);end
      4,5,6:begin value=ai-bi-(operation==5?1-ci:0);ea=operation==6?ai:(value&15);ez=((value&15)==0);ec=(value>=0);end
      7:begin ea=ai&bi;ez=(ea==0);end
      8:begin ea=ai^bi;ez=(ea==0);end
      9:begin ea=ai|bi;ez=(ea==0);end
     endcase
     bind_state(w,ai,bi,ci,zi,major>=8?5:2);step_check();
    end
  for(sub=0;sub<3;sub=sub+1)for(ai=0;ai<16;ai=ai+1)for(ci=0;ci<2;ci=ci+1)for(zi=0;zi<2;zi=zi+1)begin
   w=16'h7000|(sub<<8);ea=sub==0?((ai<<1)&15):(sub==1?(ai>>1):(ai^15));ez=(ea==0);ec=sub==0?(ai>>3):(sub==1?(ai&1):ci);
   bind_state(w,ai,0,ci,zi,2);step_check();
  end
  lockstep_enabled=0;
  bind_state(16'h0001,9,0,1,0,2);
  rom.memory[0]=16'hxxxx;rom.configuration_changed=~rom.configuration_changed;#1;
  if(!$isunknown({debug_legal,debug_next_state,retire_valid}))$fatal(1,"X ROM not observable");xchecks=xchecks+1;
  rom.memory[0]=16'hzzzz;rom.configuration_changed=~rom.configuration_changed;#1;
  if(!$isunknown({debug_legal,debug_next_state,retire_valid}))$fatal(1,"Z ROM not observable");xchecks=xchecks+1;
  bind_state(16'h8025,9,0,1,0,5);ram.memory[8'h25]=4'bxxxx;ram.configuration_changed=~ram.configuration_changed;#1;
  if(!$isunknown(retire_a))$fatal(1,"X RAM not observable");xchecks=xchecks+1;
  // X is an environment fault, not a fabricated hardware TRAP guarantee. Reset recovers known state.
  rst=1;clk=1;#1;
  if($isunknown({dbg_pc,dbg_ar,dbg_a,dbg_z,dbg_c,dbg_gpo,dbg_state}))$fatal(1,"reset failed X recovery");
  $display("M20V21_DATAPATH_PASS math_vectors=%0d xz_probes=%0d",checks,xchecks);$finish;
 end
endmodule

`undef M20V21_MANUAL_CLOCK
