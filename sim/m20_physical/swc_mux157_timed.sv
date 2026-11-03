`timescale 1ns/1ps
// Illustrative independent pin-delay model. Not SPICE, SDF, metastability or a characterized latch.
module swc_mux157_timed #(parameter real DATA_NS=2.0,SELECT_NS=2.0)
(input wire s,i0,i1,output wire y);
 wire sd,a,b;
 assign #(SELECT_NS) sd=s;
 assign #(DATA_NS) a=i0;
 assign #(DATA_NS) b=i1;
 assign y=sd?b:a;
endmodule
module swc_two_mux_dff_timed #(
 parameter integer WIDTH=1,parameter real DATA_NS=2.0,MASTER_SELECT_NS=2.0,SLAVE_SELECT_NS=2.0
)(input wire master_hold,slave_open,input wire [WIDTH-1:0] d,output wire [WIDTH-1:0] q,qm);
 genvar i;
 generate for(i=0;i<WIDTH;i=i+1)begin:g
  swc_mux157_timed #(.DATA_NS(DATA_NS),.SELECT_NS(MASTER_SELECT_NS)) m(.s(master_hold),.i0(d[i]),.i1(qm[i]),.y(qm[i]));
  swc_mux157_timed #(.DATA_NS(DATA_NS),.SELECT_NS(SLAVE_SELECT_NS)) s(.s(slave_open),.i0(q[i]),.i1(qm[i]),.y(q[i]));
 end endgenerate
endmodule
