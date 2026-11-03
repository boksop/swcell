`timescale 1ns/1ps
`default_nettype none
// External circuit: three independent level-sensitive MUX feedback elements.
// This model has no FPGA system clock, reference-model state or sequencer access.
module m11_behavioral_model #(parameter integer TPD_NS=7)(
 input wire dl_d, dl_en, dff_d, dff_clk,
 output reg dl_q, dff_q, dff_qm
);
 // Deliberately no reset / power-up initialization: feedback begins as X.
 always @(dl_d or dl_en) if(dl_en) dl_q <= #TPD_NS dl_d;
 always @(dff_d or dff_clk) if(!dff_clk) dff_qm <= #TPD_NS dff_d;
 always @(dff_qm or dff_clk) if(dff_clk) dff_q <= #TPD_NS dff_qm;
endmodule
`default_nettype wire
