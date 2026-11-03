`default_nettype none
module m11_dff_tester #(
 parameter integer PATTERN_BITS=32, RANDOM_BITS=1024
)(input wire clk, rst, start, input wire [7:0] test_id,
 output wire step_valid, input wire step_ready, step_done,
 output reg dff_d, dff_clk, output reg check_enable, output reg done);
 localparam IDLE=0, ISSUE=1, WAIT_STEP=2;
 reg [1:0] state;
 reg [7:0] selected;
 reg [1:0] init_phase, phase;
 reg [31:0] index;
 reg [31:0] iterations;
 reg [2:0] mode;
 wire data, auxiliary;
 wire advance=state==WAIT_STEP && step_done && init_phase==2 &&
              (selected>=8'h17 || phase==2);
 swc_sequence_gen pattern(.clk(clk),.rst(rst),.restart(start),
   .advance(advance),.mode(mode),.data(data),.auxiliary(auxiliary));
 assign step_valid=(state==ISSUE);
 always @* begin
   mode=3'(selected-8'h11);
   iterations=(selected==8'h16)?RANDOM_BITS:PATTERN_BITS;
   dff_d=0;dff_clk=0;check_enable=0;
   if(init_phase==1) dff_clk=1;
   if(init_phase==2) begin
     check_enable=1; dff_d=data;
     if(selected<=8'h16) dff_clk=(phase!=1);
     else if(selected==8'h17) begin dff_clk=0;dff_d=~index[0];end
     else if(selected==8'h18) begin dff_clk=1;dff_d=~index[0];end
     else begin
       // Last low-phase D is deliberately 1, so the final rising edge changes Q.
       dff_d=(index>=PATTERN_BITS-1)?1'b1:index[0];
       dff_clk=(index==PATTERN_BITS);
     end
   end
 end
 always @(posedge clk) begin
   if(rst) begin state<=IDLE;selected<=0;init_phase<=0;phase<=0;index<=0;done<=0;end
   else begin
     done<=0;
     case(state)
       IDLE:if(start) begin
         selected<=test_id;init_phase<=0;phase<=0;index<=0;state<=ISSUE;
       end
       ISSUE:if(step_ready) state<=WAIT_STEP;
       WAIT_STEP:if(step_done) begin
         state<=ISSUE;
         if(init_phase<2) init_phase<=init_phase+1'b1;
         else if(selected<=8'h16 && phase!=2) phase<=phase+1'b1;
         else begin
           phase<=0;
           if((selected==8'h19 && index==PATTERN_BITS) ||
              (selected!=8'h19 && index==iterations-1)) begin
             state<=IDLE;done<=1;
           end else index<=index+1'b1;
         end
       end
       default:state<=IDLE;
     endcase
   end
 end
endmodule
`default_nettype wire
