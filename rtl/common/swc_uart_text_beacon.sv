`default_nettype none
// Repeated fixed text, with an idle interval after the final stop bit.
module swc_uart_text_beacon #(
 parameter integer CLK_HZ=50_000_000, BAUD=115200,
 parameter integer TEXT_LEN=5, GAP_CYCLES=25_000_000,
 parameter [TEXT_LEN*8-1:0] TEXT=40'h5632300d0a
)(input wire clk, rst, output wire tx);
 localparam integer IW=(TEXT_LEN<2)?1:$clog2(TEXT_LEN);
 localparam integer GW=(GAP_CYCLES<2)?1:$clog2(GAP_CYCLES);
 localparam [1:0] SEND=0, DRAIN=1, GAP=2;
 reg [1:0] state;
 reg [IW-1:0] index;
 reg [GW-1:0] gap_count;
 wire ready;
 wire [7:0] data=TEXT[8*(TEXT_LEN-1-int'(index))+:8];
 swc_uart_tx #(.CLK_HZ(CLK_HZ),.BAUD(BAUD)) transmitter(
   .clk(clk),.rst(rst),.data(data),.valid(state==SEND),.ready(ready),.tx(tx));
 always @(posedge clk) begin
   if(rst) begin state<=SEND;index<=0;gap_count<=0;end
   else case(state)
     SEND: if(ready) begin
       if(index==IW'(TEXT_LEN-1)) state<=DRAIN;
       else index<=index+1'b1;
     end
     DRAIN: if(ready) begin state<=GAP;gap_count<=0;end
     GAP: if(gap_count==GW'(GAP_CYCLES-1)) begin state<=SEND;index<=0;end
          else gap_count<=gap_count+1'b1;
     default: begin state<=SEND;index<=0;gap_count<=0;end
   endcase
 end
 // synthesis translate_off
 initial if(TEXT_LEN<1 || GAP_CYCLES<1 || CLK_HZ<BAUD || BAUD<1)
   $fatal(1,"Invalid UART beacon parameters");
 // synthesis translate_on
endmodule
`default_nettype wire
