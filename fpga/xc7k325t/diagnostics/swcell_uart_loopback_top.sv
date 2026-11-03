`default_nettype none
// Temporary physical UART diagnostic, not the M11 functional test image.
module swcell_uart_loopback_top(
 input wire sys_clk, UART_RXD,
 output wire UART_TX, LED_G, LED_Y, LED_R,
 output wire M11_DL_D, M11_DL_EN, M11_DFF_D, M11_DFF_CLK,
 input wire M11_DL_Q, M11_DFF_Q, M11_DFF_QM
);
 reg [24:0] heartbeat_count=0;
 reg heartbeat=0, rx_seen=0;
 wire rx_sync;
 swc_input_sync #(.WIDTH(1),.STAGES(2)) rx_sampler(
   .clk(sys_clk),.rst(1'b0),.async_in(UART_RXD),.sync_out(rx_sync));
 always @(posedge sys_clk) begin
   if(heartbeat_count==25'd24_999_999) begin heartbeat_count<=0;heartbeat<=!heartbeat;end
   else heartbeat_count<=heartbeat_count+1'b1;
   if(!rx_sync) rx_seen<=1;
 end
 assign UART_TX=UART_RXD;
 assign LED_G=heartbeat;
 assign LED_Y=rx_seen;
 assign LED_R=!rx_sync;
 assign M11_DL_D=0;
 assign M11_DL_EN=1;
 assign M11_DFF_D=0;
 assign M11_DFF_CLK=0;
endmodule
`default_nettype wire
