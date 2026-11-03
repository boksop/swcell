`default_nettype none
// 8N1, LSB first; byte is accepted exactly when valid && ready.
module swc_uart_tx #(
 parameter integer CLK_HZ=100_000_000, BAUD=115200
)(input wire clk, rst, input wire [7:0] data, input wire valid,
 output wire ready, output wire tx);
 localparam integer DIVISOR=(CLK_HZ+BAUD/2)/BAUD;
 localparam integer CW=(DIVISOR<2)?1:$clog2(DIVISOR);
 reg [CW-1:0] count;
 reg [3:0] bit_index;
 reg [9:0] frame;
 reg busy;
 assign ready=!busy;
 assign tx=busy?frame[bit_index]:1'b1;
 always @(posedge clk) begin
   if(rst) begin busy<=0; count<=0; bit_index<=0; frame<=10'h3ff; end
   else if(!busy) begin
     if(valid) begin
       frame<={1'b1,data,1'b0}; busy<=1; count<=0; bit_index<=0;
     end
   end else if(count==CW'(DIVISOR-1)) begin
     count<=0;
     if(bit_index==9) begin busy<=0; bit_index<=0; end
     else bit_index<=bit_index+1'b1;
   end else count<=count+1'b1;
 end
endmodule
`default_nettype wire
