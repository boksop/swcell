`default_nettype none
// A transaction starts on valid && ready. done marks the sampling edge.
module swc_step_timer #(parameter integer STEP_CYCLES=50)(
 input wire clk, rst, valid, output wire ready, done
);
 localparam integer CW=(STEP_CYCLES<2)?1:$clog2(STEP_CYCLES);
 reg active;
 reg [CW-1:0] count;
 assign ready=!active;
 assign done=active && (count==CW'(STEP_CYCLES-1));
 always @(posedge clk) begin
   if (rst) begin active<=0; count<=0; end
   else if (!active) begin
     if (valid) begin active<=1; count<=0; end
   end else if (done) begin active<=0; count<=0; end
   else count<=count+1'b1;
 end
endmodule
`default_nettype wire
