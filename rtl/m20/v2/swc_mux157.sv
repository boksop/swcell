`default_nettype none
// One instance represents exactly one single-channel 74LVC1G157-equivalent MUX.
// Constants and plain wires are external connections, not additional cells.
module swc_mux157 (
    input  wire S,
    input  wire I0,
    input  wire I1,
    output wire Y
);
    assign Y = S ? I1 : I0;
endmodule
`default_nettype wire
