`default_nettype none
module swc_input_sync #(parameter integer WIDTH=1, STAGES=2)(
 input wire clk, rst, input wire [WIDTH-1:0] async_in,
 output wire [WIDTH-1:0] sync_out
);
 (* ASYNC_REG = "TRUE", SHREG_EXTRACT = "NO" *) reg [WIDTH-1:0] pipe [0:STAGES-1];
 integer i;
 always @(posedge clk) begin
   if (rst) for (i=0;i<STAGES;i=i+1) pipe[i] <= '0;
   else begin
     pipe[0] <= async_in;
     for (i=1;i<STAGES;i=i+1) pipe[i] <= pipe[i-1];
   end
 end
 assign sync_out=pipe[STAGES-1];
endmodule
`default_nettype wire
