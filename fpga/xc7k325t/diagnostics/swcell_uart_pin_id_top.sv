`default_nettype none
// BOTH UART pins are outputs in this image. Disconnect external TX from V20.
module swcell_uart_pin_id_top #(
 parameter integer CLK_HZ=50_000_000, BAUD=115200,
 parameter integer POR_CYCLES=5_000_000, GAP_CYCLES=25_000_000
)(input wire sys_clk,
 output wire PIN_V20_TX, PIN_W23_TX, LED_G, LED_Y, LED_R,
 output wire M11_DL_D, M11_DL_EN, M11_DFF_D, M11_DFF_CLK);
 wire rst;
 swc_power_on_reset #(.HOLD_CYCLES(POR_CYCLES)) por(.clk(sys_clk),.rst(rst));
 swc_uart_text_beacon #(.CLK_HZ(CLK_HZ),.BAUD(BAUD),
   .GAP_CYCLES(GAP_CYCLES),.TEXT(40'h5632300d0a)) v20_beacon(
   .clk(sys_clk),.rst(rst),.tx(PIN_V20_TX));
 swc_uart_text_beacon #(.CLK_HZ(CLK_HZ),.BAUD(BAUD),
   .GAP_CYCLES(GAP_CYCLES),.TEXT(40'h5732330d0a)) w23_beacon(
   .clk(sys_clk),.rst(rst),.tx(PIN_W23_TX));
 localparam integer HW=(CLK_HZ/2<2)?1:$clog2(CLK_HZ/2);
 reg [HW-1:0] heartbeat_count;
 reg heartbeat;
 always @(posedge sys_clk) begin
   if(rst) begin heartbeat_count<=0;heartbeat<=0;end
   else if(heartbeat_count==HW'(CLK_HZ/2-1)) begin
     heartbeat_count<=0;heartbeat<=!heartbeat;
   end else heartbeat_count<=heartbeat_count+1'b1;
 end
 assign LED_G=!rst && heartbeat;
 assign LED_Y=!rst;
 assign LED_R=1'b0;
 assign M11_DL_D=1'b0;
 assign M11_DL_EN=1'b1;
 assign M11_DFF_D=1'b0;
 assign M11_DFF_CLK=1'b0;
endmodule
`default_nettype wire
