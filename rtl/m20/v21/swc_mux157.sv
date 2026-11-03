`default_nettype none
module swc_mux157(input wire s, input wire i0, input wire i1, output wire y);
    assign y = s ? i1 : i0;
endmodule
`default_nettype wire
