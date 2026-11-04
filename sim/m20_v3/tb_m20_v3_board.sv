`timescale 1ns/1ps
module tb_m20_v3_board #(parameter PONG_FILE="",SNAKE_FILE="",
 parameter[11:0] SNAKE_TICK_DONE=m20_v3_game_pkg::SNAKE_DONE);
 import swc_oled_font_pkg::*;
 reg clk=0;always #10 clk=~clk;
 reg[8:0] pins=9'h1ff;reg rx=1;
 wire tx,res,dc,sck,mosi,cs;wire[7:0] led;
 swcell_m20_v3_top #(.PONG_FILE(PONG_FILE),.SNAKE_FILE(SNAKE_FILE),.SNAKE_TICK_DONE(SNAKE_TICK_DONE),.POR_CYCLES(20),.DEBOUNCE_CYCLES(12),
  .UART_BAUD(1000000),.REPORT_CYCLES(100000),.PONG_HZ(5000),.SNAKE_HZ(5000),
  .OLED_RESET_CYCLES(200),.OLED_RELEASE_CYCLES(200),.OLED_ON_WAIT_CYCLES(200)) dut(
  .sys_clk(clk),.RST_N(pins[8]),.KEY0(pins[0]),.KEY1(pins[1]),.KEY2(pins[2]),.KEY3(pins[3]),
  .KEY4(pins[4]),.KEY5(pins[5]),.KEY6(pins[6]),.KEY7(pins[7]),.UART_RXD(rx),
  .UART_TX(tx),.OLED_RST_N(res),.OLED_DC(dc),.OLED_SCK(sck),.OLED_MOSI(mosi),.OLED_CS_N(cs),
  .LED0(led[0]),.LED1(led[1]),.LED2(led[2]),.LED3(led[3]),.LED4(led[4]),.LED5(led[5]),.LED6(led[6]),.LED7(led[7]));
 ssd1306_spi_model panel(.rst_n(res),.cs_n(cs),.dc(dc),.sck(sck),.mosi(mosi));
 integer raw,uart_bytes=0,pong_frames=0,snake_frames=0,boot_frames=0,up_samples=0,previous_up_samples;
 always @(posedge clk)if(dut.input0_ack&&dut.consumed_keys[0])up_samples=up_samples+1;
 string outdir=".";reg[7:0] value;
 initial begin if($value$plusargs("OUT=%s",outdir))begin end raw=$fopen({outdir,"/uart.jsonl"},"wb");end
 always begin
  @(negedge tx);#500;if(tx!==0)$fatal(1,"V3_UART_START");
  for(integer b=0;b<8;b=b+1)begin #1000;value[b]=tx;end
  #1000;if(tx!==1)$fatal(1,"V3_UART_STOP");
  $fwrite(raw,"%c",value);$fflush(raw);uart_bytes=uart_bytes+1;
 end
 always @(posedge dut.display.done)begin
  integer x,y,p;
  #1;
  if(panel.seg_remap!==0||panel.com_reverse!==0||!panel.display_on||panel.inverse)$fatal(1,"V3_OLED_MODE");
  if(!dut.display.snapshot_valid)begin
   for(integer column=0;column<128;column=column+1)begin
    if(panel.ram[128+column]!==font_column(8'("KEY5: START     " >> ((15-column/8)*8)),3'(column%8)))
     $fatal(1,"V3_BOOT_KEY_HINT_PIXEL column=%0d",column);
   end
   boot_frames=boot_frames+1;
  end
  if(dut.display.snapshot_valid)begin
   if(dut.display.snapshot_game)begin
    x=8*dut.display.snapshot[7*4+:4]+3;y=8+7*dut.display.snapshot[8*4+:4]+3;
    if(panel.ram[(y/8)*128+x][y%8]!==1)$fatal(1,"V3_SNAKE_FOOD_PIXEL");
    snake_frames=snake_frames+1;
    $writememh({outdir,"/snake_oled.memh"},panel.ram);
   end else begin
    x=8*dut.display.snapshot[0+:4]+3;y=8+6*dut.display.snapshot[4+:4]+2;
    if(panel.ram[(y/8)*128+x][y%8]!==1)$fatal(1,"V3_PONG_BALL_PIXEL");
    y=8+6*dut.display.snapshot[16+:4]+1;
    if(panel.ram[(y/8)*128+1][y%8]!==1)$fatal(1,"V3_PONG_PADDLE_PIXEL");
    pong_frames=pong_frames+1;
    $writememh({outdir,"/pong_oled.memh"},panel.ram);
   end
  end
 end
 task command_byte(input[7:0] ch);
  @(negedge clk);rx=0;#1000;
  for(integer b=0;b<8;b=b+1)begin rx=ch[b];#1000;end
  rx=1;#2000;
 endtask
 task key_press(input integer physical,input[5:0] logical_mask);
  @(negedge clk);pins[physical]=0;repeat(100)@(negedge clk);
  if(dut.raw_keys!==logical_mask)$fatal(1,"V3_PHYSICAL_KEYS pin=%d logical=%h expected=%h",physical,dut.raw_keys,logical_mask);
  repeat(100000)@(negedge clk);
  pins[physical]=1;repeat(100)@(negedge clk);
  if(dut.raw_keys!==0)$fatal(1,"V3_KEY_RELEASE");
 endtask
 reg[63:0] stopped_count;
 initial begin
  wait(pong_frames>=1);
  key_press(2,1);key_press(0,2);key_press(3,4);key_press(1,8);
  key_press(4,0);
  if(!dut.run_requested)$fatal(1,"V3_CENTER_KEY_MUST_NOT_PAUSE");
  // Reproduce the observed F05 page: paused CPU reset, no valid game frame.
  key_press(7,0);
  key_press(8,0);
  if(dut.frame_valid||dut.run_requested||dut.game||dut.pc!=0)$fatal(1,"V3_BOOT_STOPPED_RESET_FIXTURE");
  wait(boot_frames>=1);
  stopped_count=dut.microcycles;
  key_press(7,0);
  if(dut.run_requested||dut.microcycles!=stopped_count)$fatal(1,"V3_BOOT_MUST_NOT_REQUIRE_KEY7");
  key_press(5,16);
  if(!dut.run_requested||dut.game||!dut.frame_valid)$fatal(1,"V3_KEY_A_MUST_START_CURRENT_GAME_FROM_BOOT");
  key_press(5,16);
  if(!dut.game||!dut.run_requested)$fatal(1,"V3_KEY_A_MUST_SELECT_SNAKE_WITHOUT_PAUSING");
  // Snake boot clears all RAM; wait until this really is a game page.
  wait(dut.frame_valid&&dut.frame_game&&dut.game);
  key_press(7,0);
  if(dut.run_requested||!dut.game)$fatal(1,"V3_KEY7_MUST_PAUSE_WITHOUT_SWITCHING");
  key_press(5,16);
  if(dut.game||dut.run_requested)$fatal(1,"V3_KEY_A_MUST_SELECT_PONG_WHILE_PAUSED");
  key_press(5,16);
  if(!dut.run_requested||dut.game||!dut.frame_valid)$fatal(1,"V3_KEY_A_MUST_ENTER_SELECTED_PONG");
  key_press(7,0);
  if(dut.run_requested||dut.game)$fatal(1,"V3_KEY7_MUST_PAUSE_GAME");
  key_press(7,0);
  if(!dut.run_requested||dut.game)$fatal(1,"V3_KEY7_MUST_RESUME_WITHOUT_SWITCHING");
  key_press(6,32);
  command_byte(" ");wait(!dut.run_requested);wait(!dut.active);
  // A valid short tap fully released while stopped must reach a later CPU IN0.
  previous_up_samples=up_samples;
  @(negedge clk);pins[2]=0;repeat(30)@(negedge clk);pins[2]=1;repeat(30)@(negedge clk);
  if(dut.raw_keys!=0||dut.queued_keys==0)$fatal(1,"V3_SHORT_TAP_NOT_BUFFERED");
  command_byte(" ");wait(dut.run_requested);wait(up_samples>previous_up_samples);
  command_byte(" ");wait(!dut.run_requested);wait(!dut.active);
  stopped_count=dut.microcycles;repeat(1000)@(negedge clk);
  if(dut.microcycles!=stopped_count)$fatal(1,"V3_UART_STOP_COMMAND");
  command_byte("n");wait(dut.microcycles==stopped_count+1);wait(!dut.active);#1;
  if(dut.microcycles!=stopped_count+1)$fatal(1,"V3_UART_STEP_COMMAND");
  command_byte("s");wait(dut.game);
  command_byte(" ");wait(dut.run_requested);
  wait(snake_frames>=1);repeat(100000)@(negedge clk);
  if(dut.errors!=0)$fatal(1,"V3_BOARD_CPU_ERRORS");
  if(dut.phase_trace!=8'hb8)$fatal(1,"V3_PHASE_TRACE");
  // Drain one complete UART record. This affects telemetry scheduling only.
  force dut.report_timer=32'hffffffff;
  wait(dut.reporter.ready&&dut.reporter.uart_ready);#2000;
  $fclose(raw);
  $display("M20_V3_BOARD_PASS pong_frames=%0d snake_frames=%0d boot_frames=%0d uart_bytes=%0d key_mapping=6 boot_entry_key=5 game_select_key=5 pause_key=7 spi_hz=10000000",pong_frames,snake_frames,boot_frames,uart_bytes);
  $finish;
 end
 initial begin #200000000;$fatal(1,"V3_BOARD_TIMEOUT");end
endmodule
