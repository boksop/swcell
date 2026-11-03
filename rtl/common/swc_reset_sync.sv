`default_nettype none
module swc_reset_sync(input wire clk, reset_n, output wire rst);
 (* ASYNC_REG="TRUE" *) reg [1:0] reset_pipe;
 always @(posedge clk or negedge reset_n)
   if (!reset_n) reset_pipe <= 2'b11;
   else reset_pipe <= {reset_pipe[0],1'b0};
 assign rst=reset_pipe[1];
endmodule
`default_nettype wire
