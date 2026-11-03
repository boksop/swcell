`timescale 1ns/1ps
// FPGA IO observer/provider only: registered keys and observed GPO, no CPU computation.
module m20_v23_io_model(input wire sys_clk,key_sample_ce,observe_ce,
 input wire [5:0] requested_keys,input wire [3:0] gpo,
 output logic [5:0] keys=0,output logic [3:0] observed_gpo);
 always @(posedge sys_clk)begin
  if(key_sample_ce)keys<=requested_keys;
  if(observe_ce)observed_gpo<=gpo;
 end
endmodule
