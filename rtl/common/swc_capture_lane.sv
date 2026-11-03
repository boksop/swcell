`default_nettype none
// IOB sample followed by matched expected/tag pipeline. Result freezes at LIMIT.
module swc_capture_lane #(parameter [63:0] LIMIT=64'd1000000)(
 input wire clk,rst,enable,sample_ce,actual,expected,
 input wire [30:0] expected_state,
 output reg done,
 output reg [63:0] total_bits,errors,first_cycle,
 output reg first_expected,first_actual,
 output reg [30:0] first_state,start_state,
 output wire error_event
);
 (* IOB="TRUE" *) reg captured;
 reg expected_pipe,valid_pipe;
 reg [30:0] state_pipe;
 reg [63:0] issued;
 assign error_event=valid_pipe && (captured!=expected_pipe);
 // No reset/enable on IOB data register: map to an ordinary IOB input FF.
 always @(posedge clk) captured<=actual;
 always @(posedge clk) begin
   if(rst) begin
     expected_pipe<=0;valid_pipe<=0;state_pipe<=0;issued<=0;
     total_bits<=0;errors<=0;first_cycle<=0;first_expected<=0;
     first_actual<=0;first_state<=0;start_state<=0;done<=0;
   end else begin
     valid_pipe<=enable && sample_ce && issued<LIMIT;
     if(enable && sample_ce && issued<LIMIT) begin
       expected_pipe<=expected;state_pipe<=expected_state;issued<=issued+1'b1;
       if(issued==0) start_state<=expected_state;
     end
     if(valid_pipe) begin
       total_bits<=total_bits+1'b1;
       if(error_event) begin
         errors<=errors+1'b1;
         if(errors==0) begin
           first_cycle<=total_bits+1'b1;first_expected<=expected_pipe;
           first_actual<=captured;first_state<=state_pipe;
         end
       end
       if(total_bits==LIMIT-1) done<=1;
     end
   end
 end
 // synthesis translate_off
 initial if(LIMIT==0) $fatal(1,"Capture LIMIT must be positive");
 // synthesis translate_on
endmodule
`default_nettype wire
