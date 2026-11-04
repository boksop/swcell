`timescale 1ns/1ps
`default_nettype none
// CONNECTION PROPOSAL ONLY. Untimed RTL collapses the delay chain to a wire.
// Not a validated non-overlap generator or an FPGA LUT implementation.
// Each swc_phase_mux157 instance maps to one external NC7SZ157.
module swc_phase_mux157(input wire s,i0,i1,output wire y);
 assign y=s?i1:i0;
endmodule

module swc157_phase_feedforward #(
 parameter integer DELAY_STAGES=8
)(input wire clk_ref,safe_hold,
 output wire master_hold,slave_open,delayed_ref);
 wire [DELAY_STAGES:0] delay_tap;
 wire h_raw,s_raw;
 assign delay_tap[0]=clk_ref;
 generate for(genvar i=0;i<DELAY_STAGES;i=i+1)begin:g_delay
  swc_phase_mux157 buffer157(.s(1'b0),.i0(delay_tap[i]),.i1(1'b0),.y(delay_tap[i+1]));
 end endgenerate
 assign delayed_ref=delay_tap[DELAY_STAGES];
 // H=C|Cd; S=C&Cd. The fast C controls both selector inputs.
 swc_phase_mux157 decode_h(.s(clk_ref),.i0(delayed_ref),.i1(1'b1),.y(h_raw));
 swc_phase_mux157 decode_s(.s(clk_ref),.i0(1'b0),.i1(delayed_ref),.y(s_raw));
 // Asserted hold closes both CPU latch groups; not a complete RUN/STEP controller.
 swc_phase_mux157 hold_h(.s(safe_hold),.i0(h_raw),.i1(1'b1),.y(master_hold));
 swc_phase_mux157 hold_s(.s(safe_hold),.i0(s_raw),.i1(1'b0),.y(slave_open));
endmodule
`default_nettype wire
