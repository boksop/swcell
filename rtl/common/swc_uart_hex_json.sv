`default_nettype none
// '#' characters are replaced by successive payload nibbles, MSB first.
// Atomic snapshot and UART ready/valid; one complete line at a time.
module swc_uart_hex_json #(
 parameter integer CLK_HZ=50000000,BAUD=115200,HEX_DIGITS=1,
 parameter FORMAT="{\"value\":\"#\"}\n"
)(input wire clk,rst,request,input wire[HEX_DIGITS*4-1:0] payload,
 output wire tx,output wire ready);
 localparam integer LENGTH=$bits(FORMAT)/8;
 localparam [LENGTH*8-1:0] TEXT=FORMAT;
 logic sending=0;logic[15:0] index=0,nibble=0;
 logic[HEX_DIGITS*4-1:0] held;
 wire uart_ready;wire[7:0] symbol=TEXT[(LENGTH-1-index)*8+:8];
 wire[3:0] value=held[(HEX_DIGITS-1-nibble)*4+:4];
 wire[7:0] encoded=value<10?(8'h30+{4'b0,value}):(8'h41+{4'b0,value}-8'd10);
 assign ready=!sending;
 swc_uart_tx #(.CLK_HZ(CLK_HZ),.BAUD(BAUD)) uart(.clk(clk),.rst(rst),.data(symbol==8'h23 ? encoded : symbol),.valid(sending),.ready(uart_ready),.tx(tx));
 always_ff @(posedge clk)begin
  if(rst)begin sending<=0;index<=0;nibble<=0;held<=0;end
  else if(!sending)begin if(request)begin held<=payload;index<=0;nibble<=0;sending<=1;end end
  else if(uart_ready)begin
   if(symbol==8'h23)nibble<=nibble+1'b1;
   if(index==LENGTH-1)begin sending<=0;index<=0;end else index<=index+1'b1;
  end
 end
endmodule
`default_nettype wire
