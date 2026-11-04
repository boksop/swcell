`timescale 1ns/1ps
// Use production SPI/frame-gap defaults; accelerate only initial reset waits.
module tb_oled_refresh;
 reg clk=0;always #10 clk=~clk;
 wire res,dc,sck,mosi,cs;wire display_on,inverse;
 integer data_bytes,command_bytes,transactions;
 swcell_oled_keys_top #(.POR_CYCLES(20),.RESET_CYCLES(200),
  .RELEASE_CYCLES(200),.ON_WAIT_CYCLES(200)) dut(
  .sys_clk(clk),.RST_N(1'b1),.KEY0(1'b1),.KEY1(1'b1),.KEY2(1'b1),.KEY3(1'b1),
  .KEY4(1'b1),.KEY5(1'b1),.KEY6(1'b1),.KEY7(1'b1),.UART_RXD(1'b1),
  .OLED_RST_N(res),.OLED_DC(dc),.OLED_SCK(sck),.OLED_MOSI(mosi),.OLED_CS_N(cs));
 ssd1306_spi_model panel(.rst_n(res),.cs_n(cs),.dc(dc),.sck(sck),.mosi(mosi),
  .display_on(display_on),.inverse(inverse),.data_bytes(data_bytes),
  .command_bytes(command_bytes),.transactions(transactions));
 // The reusable driver's default preserves the original A1/C8 orientation.
 wire base_res,base_dc,base_sck,base_mosi,base_cs,base_ready;
 swc_ssd1306 #(.RESET_CYCLES(200),.RELEASE_CYCLES(200),.ON_WAIT_CYCLES(200)) baseline(
  .clk(clk),.rst(dut.rst),.frame_start(1'b0),.inverse(1'b0),.pixel_valid(1'b1),.pixel_data(8'h00),
  .initialized(base_ready),.oled_rst_n(base_res),.oled_dc(base_dc),
  .oled_cs_n(base_cs),.oled_sck(base_sck),.oled_mosi(base_mosi));
 ssd1306_spi_model base_panel(.rst_n(base_res),.cs_n(base_cs),.dc(base_dc),
  .sck(base_sck),.mosi(base_mosi));
 integer edges=0;real previous_edge=0;
 always @(negedge cs)edges=0;
 always @(posedge sck)if(!cs)begin
  if(edges>0&&$realtime-previous_edge!=100.0)$fatal(1,"PRODUCTION_SPI_NOT_10MHZ");
  edges=edges+1;previous_edge=$realtime;
 end
 always @(negedge sck)if(!cs&&edges>0)
  if($realtime-previous_edge!=40.0)$fatal(1,"PRODUCTION_SPI_HIGH_NOT_40NS");
 integer cycles=0,starts_at=0,last_done=0,period=0,previous_period=0,count=0;
 always @(posedge clk)begin
  cycles=cycles+1;
  if(dut.frame_start)starts_at=cycles;
  if(dut.frame_done)begin
   count=count+1;
   if(count>1)begin
    period=cycles-last_done;
    if(count>2&&period!=previous_period)$fatal(1,"UNSTABLE_FRAME_PERIOD");
    previous_period=period;
   end
   last_done=cycles;
   if(count==3)begin
    if(period>1000000)$fatal(1,"PRODUCTION_FRAME_RATE_BELOW_50HZ");
    if(panel.inverse_commands!=1)$fatal(1,"STATIC_MODE_RESENDS_INVERSE");
    if(base_panel.seg_remap!==1||base_panel.com_reverse!==1||!base_ready)$fatal(1,"DEFAULT_ORIENTATION");
    if(panel.seg_remap!==0||panel.com_reverse!==0)$fatal(1,"BOARD_ROTATED_ORIENTATION");
    $display("OLED_REFRESH_PASS spi_hz=10000000 frame_cycles=%0d transfer_cycles=%0d frame_hz=%f",period,cycles-starts_at,50000000.0/period);
    $finish;
   end
  end
 end
 initial begin #150000000;$fatal(1,"OLED_REFRESH_TIMEOUT");end
endmodule
