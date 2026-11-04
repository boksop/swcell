`timescale 1ns/1ps
`default_nettype none
// One external NC7SZ157: structural truth table only, no propagation model.
module swc_ff16_mux157(input wire s,i0,i1,output wire y);
 assign y=s?i1:i0;
endmodule
`default_nettype wire
