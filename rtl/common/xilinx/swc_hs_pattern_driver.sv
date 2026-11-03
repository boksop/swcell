`default_nettype none
// Reusable quarter-phase output driver. PRBS implementation is shared with Phase 1.
module swc_hs_pattern_driver #(parameter integer PATTERN=5)(
 input wire clk,rst,ce,stopped,
 output wire pin_data,advancing,bit_value,
 output reg launched_data,output reg [30:0] launched_state,
 output wire [30:0] sequence_state
);
 reg [7:0] warmup;reg [2:0] index;
 wire random_bit;
 assign advancing=warmup>=32 && !stopped;
 swc_prbs31 sequence_generator(.clk(clk),.rst(rst),.restart(1'b0),
   .advance(ce && advancing),.bit_out(random_bit),.state_out(sequence_state));
 assign bit_value=(PATTERN==0)?1'b0:(PATTERN==1)?1'b1:
                  (PATTERN==2)?index[0]:(PATTERN==3)?index[1]:random_bit;
 wire next_data=advancing?bit_value:launched_data;
 always @(posedge clk) begin
   if(rst) begin warmup<=0;index<=0;launched_data<=0;launched_state<=0;end
   else if(ce) begin
     if(warmup!=255) warmup<=warmup+1'b1;
     if(advancing) begin
       launched_data<=bit_value;launched_state<=sequence_state;index<=index+1'b1;
     end
   end
 end
 ODDR #(.DDR_CLK_EDGE("SAME_EDGE"),.SRTYPE("ASYNC"),.INIT(1'b0)) data_output(
   .C(clk),.CE(ce),.D1(next_data),.D2(next_data),.R(rst),.S(1'b0),.Q(pin_data));
endmodule
`default_nettype wire
