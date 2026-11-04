`timescale 1ns/1ps
`default_nettype none
// Fixed 20-device physical connection model. TAP_STAGES represents exactly ONE
// fitted 0-ohm link, not a runtime logic selector. Untimed RTL has no dead time.
module swc_ff16_phasegen #(
 parameter integer TAP_STAGES=8
)(input wire clk_ref,safe_hold,
 output wire master_hold,slave_open,delayed_ref,
 output wire tap4,tap8,tap12,tap16,h_raw,s_raw);
 wire [16:0] chain;
 assign chain[0]=clk_ref;
 // Every instance remains in this physical model for every legal TAP_STAGES.
 swc_ff16_mux157 u_delay01(.s(1'b0),.i0(chain[0]), .i1(1'b0),.y(chain[1]));
 swc_ff16_mux157 u_delay02(.s(1'b0),.i0(chain[1]), .i1(1'b0),.y(chain[2]));
 swc_ff16_mux157 u_delay03(.s(1'b0),.i0(chain[2]), .i1(1'b0),.y(chain[3]));
 swc_ff16_mux157 u_delay04(.s(1'b0),.i0(chain[3]), .i1(1'b0),.y(chain[4]));
 swc_ff16_mux157 u_delay05(.s(1'b0),.i0(chain[4]), .i1(1'b0),.y(chain[5]));
 swc_ff16_mux157 u_delay06(.s(1'b0),.i0(chain[5]), .i1(1'b0),.y(chain[6]));
 swc_ff16_mux157 u_delay07(.s(1'b0),.i0(chain[6]), .i1(1'b0),.y(chain[7]));
 swc_ff16_mux157 u_delay08(.s(1'b0),.i0(chain[7]), .i1(1'b0),.y(chain[8]));
 swc_ff16_mux157 u_delay09(.s(1'b0),.i0(chain[8]), .i1(1'b0),.y(chain[9]));
 swc_ff16_mux157 u_delay10(.s(1'b0),.i0(chain[9]), .i1(1'b0),.y(chain[10]));
 swc_ff16_mux157 u_delay11(.s(1'b0),.i0(chain[10]),.i1(1'b0),.y(chain[11]));
 swc_ff16_mux157 u_delay12(.s(1'b0),.i0(chain[11]),.i1(1'b0),.y(chain[12]));
 swc_ff16_mux157 u_delay13(.s(1'b0),.i0(chain[12]),.i1(1'b0),.y(chain[13]));
 swc_ff16_mux157 u_delay14(.s(1'b0),.i0(chain[13]),.i1(1'b0),.y(chain[14]));
 swc_ff16_mux157 u_delay15(.s(1'b0),.i0(chain[14]),.i1(1'b0),.y(chain[15]));
 swc_ff16_mux157 u_delay16(.s(1'b0),.i0(chain[15]),.i1(1'b0),.y(chain[16]));
 assign tap4=chain[4];
 assign tap8=chain[8];
 assign tap12=chain[12];
 assign tap16=chain[16];
 generate
  if(TAP_STAGES==4)begin:g_tap4
   assign delayed_ref=tap4;
  end else if(TAP_STAGES==8)begin:g_tap8
   assign delayed_ref=tap8;
  end else if(TAP_STAGES==12)begin:g_tap12
   assign delayed_ref=tap12;
  end else if(TAP_STAGES==16)begin:g_tap16
   assign delayed_ref=tap16;
  end else begin:g_invalid
   assign delayed_ref=1'bx;
   initial $fatal(1,"TAP_STAGES must be 4,8,12,16");
  end
 endgenerate
 swc_ff16_mux157 u_decode_h(.s(clk_ref),.i0(delayed_ref),.i1(1'b1),.y(h_raw));
 swc_ff16_mux157 u_decode_s(.s(clk_ref),.i0(1'b0),.i1(delayed_ref),.y(s_raw));
 swc_ff16_mux157 u_hold_h(.s(safe_hold),.i0(h_raw),.i1(1'b1),.y(master_hold));
 swc_ff16_mux157 u_hold_s(.s(safe_hold),.i0(s_raw),.i1(1'b0),.y(slave_open));
endmodule
`default_nettype wire
