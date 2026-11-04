`default_nettype none
// 8N1 command receiver, center samples. rx must already be synchronized.
module swc_uart_rx #(parameter integer CLK_HZ=50000000,BAUD=115200)(
 input wire clk,rst,rx,output logic[7:0] data,output logic valid,framing_error);
 localparam integer BIT_TICKS=(CLK_HZ+BAUD/2)/BAUD;
 logic[15:0] timer=0;logic[3:0] state=0;logic[7:0] shift=0;
 always_ff @(posedge clk)begin
  valid<=0;framing_error<=0;
  if(rst)begin state<=0;timer<=0;data<=0;shift<=0;end
  else if(state==0)begin if(!rx)begin state<=1;timer<=16'(BIT_TICKS/2-1);end end
  else if(timer!=0)timer<=timer-1'b1;
  else begin
   timer<=16'(BIT_TICKS-1);
   if(state==1)begin if(rx)state<=0;else state<=2;end
   else if(state<10)begin shift[state-2]<=rx;state<=state+1'b1;end
   else begin state<=0;if(rx)begin data<=shift;valid<=1;end else framing_error<=1;end
  end
 end
endmodule
`default_nettype wire
