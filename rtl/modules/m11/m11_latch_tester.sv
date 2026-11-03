`default_nettype none
module m11_latch_tester #(
 parameter integer PATTERN_STEPS=32, RANDOM_STEPS=1024
)(input wire clk, rst, start, input wire [7:0] test_id,
 output wire step_valid, input wire step_ready, step_done,
 output reg dl_d, dl_en, output reg check_enable, output reg done);
 localparam IDLE=0, ISSUE=1, WAIT_STEP=2;
 reg [1:0] state;
 reg [7:0] selected;
 reg [31:0] index;
 reg [31:0] last_index;
 reg [2:0] mode;
 wire data, auxiliary;
 wire advance=state==WAIT_STEP && step_done && index!=0;
 swc_sequence_gen pattern(.clk(clk),.rst(rst),.restart(start),
   .advance(advance),.mode(mode),.data(data),.auxiliary(auxiliary));
 assign step_valid=(state==ISSUE);
 always @* begin
   dl_d=0; dl_en=1; check_enable=0; last_index=1; mode=2;
   case(selected)
     8'h01:begin last_index=1; if(index==1) check_enable=1; end
     8'h02:begin last_index=1; if(index==1) begin dl_d=1;check_enable=1;end end
     8'h03,8'h04,8'h05:begin
       last_index=(selected==8'h04)?4:3;
       if(index==1) dl_d=1;
       if(index==2) begin dl_d=1;dl_en=0;end
       if(index==3) begin dl_d=0;dl_en=(selected==8'h05);end
       if(index==4) begin dl_d=1;dl_en=0;end
       check_enable=(index==last_index);
     end
     8'h06:begin
       last_index=PATTERN_STEPS+1;
       if(index!=0) dl_en=0;
       if(index>=2) begin dl_d=index[0];check_enable=1;end
     end
     8'h07:begin
       last_index=PATTERN_STEPS;
       if(index!=0) begin dl_d=data;check_enable=1;end
     end
     8'h08:begin
       mode=5; last_index=RANDOM_STEPS;
       if(index!=0) begin dl_d=data;dl_en=auxiliary;check_enable=1;end
     end
     default:begin end
   endcase
 end
 always @(posedge clk) begin
   if(rst) begin state<=IDLE;selected<=0;index<=0;done<=0;end
   else begin
     done<=0;
     case(state)
       IDLE:if(start) begin selected<=test_id; index<=0;state<=ISSUE;end
       ISSUE:if(step_ready) state<=WAIT_STEP;
       WAIT_STEP:if(step_done) begin
         if(index==last_index) begin state<=IDLE;done<=1;end
         else begin index<=index+1'b1;state<=ISSUE;end
       end
       default:state<=IDLE;
     endcase
   end
 end
endmodule
`default_nettype wire
