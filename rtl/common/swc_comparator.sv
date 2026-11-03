`default_nettype none
module swc_comparator #(parameter integer WIDTH=3)(
 input wire [WIDTH-1:0] actual, expected, mask,
 output wire [WIDTH-1:0] mismatch
);
 // Case inequality also treats X/Z in simulation as a failed check.
 genvar i;
 generate for(i=0;i<WIDTH;i=i+1) begin:g_compare
   assign mismatch[i]=mask[i] && (actual[i] !== expected[i]);
 end endgenerate
endmodule
`default_nettype wire
