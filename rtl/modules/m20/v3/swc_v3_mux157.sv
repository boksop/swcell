`default_nettype none
// The primitive preserves the original u_nNNNN hierarchy and one LUT per MUX.
(* KEEP_HIERARCHY="yes", DONT_TOUCH="yes" *)
module swc_v3_mux157(input wire s,i0,i1,output wire y);
`ifdef SWC_V3_XILINX
 (* DONT_TOUCH="yes" *) LUT3 #(.INIT(8'hca)) cell_mux(.I0(i0),.I1(i1),.I2(s),.O(y));
`else
 assign y=s?i1:i0;
`endif
endmodule
// Explicit feedback, deliberately not an FPGA FF. Do NOT suppress LUTLP-1.
module swc_v3_mux_storage(input wire d,master_hold,slave_open,output wire q);
 wire qm;
 swc_v3_mux157 master(.s(master_hold),.i0(d),.i1(qm),.y(qm));
 swc_v3_mux157 slave(.s(slave_open),.i0(q),.i1(qm),.y(q));
endmodule
`default_nettype wire
