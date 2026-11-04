`timescale 1ns/1ps
// FPGA service events derived only from the actual reference input and sys_clk.
module swc_ffcd_service #(
 parameter integer RAM_TICK=4,PREVIEW_TICK=14,OBSERVE_TICK=4,ROM_TICK=8,CONTROL_TICK=12
)(input wire sys_clk,reset,clk_ref,cycle_active,
 output wire ref_rise_ce,ref_fall_ce,ram_sample_ce,preview_ce,write_ce,observe_ce,rom_read_ce,control_window,
 output logic commit_clk=0,output logic [15:0] age=0,output wire ref_level);
 (* ASYNC_REG="TRUE" *)logic ref_meta=0,ref_sync=0;
 logic ref_prev=0;
 assign ref_level=ref_sync;
 assign ref_rise_ce=ref_sync&&!ref_prev;
 assign ref_fall_ce=!ref_sync&&ref_prev;
 assign ram_sample_ce=cycle_active&&!ref_sync&&age==RAM_TICK;
 assign preview_ce=cycle_active&&!ref_sync&&age==PREVIEW_TICK;
 assign write_ce=cycle_active&&ref_sync&&age==0;
 assign observe_ce=cycle_active&&ref_sync&&age==OBSERVE_TICK;
 assign rom_read_ce=cycle_active&&ref_sync&&age==ROM_TICK;
 assign control_window=ref_sync&&age==CONTROL_TICK;
 always_ff @(posedge sys_clk)begin
  ref_meta<=clk_ref;ref_sync<=ref_meta;ref_prev<=ref_sync;
  commit_clk<=preview_ce;
  if(reset)begin ref_meta<=0;ref_sync<=0;ref_prev<=0;age<=0;commit_clk<=0;end
  else if(ref_rise_ce || ref_fall_ce)age<=0;
  else if(age!=16'hffff)age<=age+1'b1;
 end
endmodule

module swc_ffcd_ref_div #(parameter integer HALF_TICKS=25)(input wire sys_clk,reset,output logic clk_ref=0);
 integer count=0;
 always_ff @(posedge sys_clk)begin
  if(reset)begin count<=0;clk_ref<=0;end
  else if(count==HALF_TICKS-1)begin count<=0;clk_ref<=~clk_ref;end
  else count<=count+1;
 end
endmodule
