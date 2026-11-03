`default_nettype none
// Xilinx FPGA configuration INIT values start the hold counter and reset pipeline.
// No external reset, gated clock, analog POR or run-time voltage detector is used.
module swc_power_on_reset #(parameter integer HOLD_CYCLES=5_000_000)(
 input wire clk, output wire rst
);
 localparam integer CW=(HOLD_CYCLES<2)?1:$clog2(HOLD_CYCLES);
 reg [CW-1:0] count = '0;
 reg hold_reset = 1'b1;
 (* ASYNC_REG="TRUE", SHREG_EXTRACT="NO" *) reg [1:0] release_pipe = 2'b11;
 always @(posedge clk) begin
   if(hold_reset) begin
     if(count==CW'(HOLD_CYCLES-1)) hold_reset<=1'b0;
     else count<=count+1'b1;
   end
   release_pipe<={release_pipe[0],hold_reset};
 end
 assign rst=release_pipe[1];
 // synthesis translate_off
 initial if(HOLD_CYCLES<1) $fatal(1,"POR HOLD_CYCLES must be >=1");
 // synthesis translate_on
endmodule
`default_nettype wire
