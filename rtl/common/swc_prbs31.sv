`default_nettype none
module swc_prbs31 #(parameter [30:0] SEED=31'h13579bdf)(
 input wire clk, rst, restart, advance,
 output wire bit_out, output wire [30:0] state_out
);
 reg [30:0] state;
 // x^31+x^28+1: left shift, feedback state[30] XOR state[27].
 always @(posedge clk) begin
   if (rst || restart) state <= (SEED==0)?31'b1:SEED;
   else if (advance) state <= {state[29:0],state[30]^state[27]};
 end
 assign bit_out=state[30];
 assign state_out=state;
endmodule
`default_nettype wire
