`timescale 1ns/1ps
module tb_oled_keys;
 reg clk=0;always #10 clk=~clk;
 reg[8:0] pins=9'h1ff;reg rx=1;
 wire[7:0] led_n;wire tx,res,dc,sck,mosi,cs;
 swcell_oled_keys_top #(.UART_BAUD(1000000),.POR_CYCLES(20),.DEBOUNCE_CYCLES(12),
  .RESET_CYCLES(200),.RELEASE_CYCLES(200),.ON_WAIT_CYCLES(200),
  .FRAME_GAP_CYCLES(100),.PATTERN_FRAMES(1),.LONG_HOLD_CYCLES(200000),.REPORT_CYCLES(1000000)) dut(
  .sys_clk(clk),.RST_N(pins[8]),.KEY0(pins[0]),.KEY1(pins[1]),.KEY2(pins[2]),.KEY3(pins[3]),.KEY4(pins[4]),.KEY5(pins[5]),.KEY6(pins[6]),.KEY7(pins[7]),.UART_RXD(rx),
  .OLED_RST_N(res),.OLED_DC(dc),.OLED_SCK(sck),.OLED_MOSI(mosi),.OLED_CS_N(cs),
  .LED0(led_n[0]),.LED1(led_n[1]),.LED2(led_n[2]),.LED3(led_n[3]),.LED4(led_n[4]),.LED5(led_n[5]),.LED6(led_n[6]),.LED7(led_n[7]),.UART_TX(tx));
 wire display_on,inverse;integer data_bytes,command_bytes,transactions;
 ssd1306_spi_model panel(.rst_n(res),.cs_n(cs),.dc(dc),.sck(sck),.mosi(mosi),.display_on(display_on),.inverse(inverse),.data_bytes(data_bytes),.command_bytes(command_bytes),.transactions(transactions));
 integer frames_checked=0,live_checked=0,selftest_checked=0,uart_bytes=0;integer raw;string outdir=".";
 reg[7:0] received;reg[7:0] expected;reg[63:0] checked_masks=0;
 integer expected_inverse_commands=1;reg previous_inverse=0;
 initial begin if($value$plusargs("OUT=%s",outdir))begin end raw=$fopen({outdir,"/uart.jsonl"},"wb");end
 // Real 8N1 wire decoder, independent of UART internal state.
 always begin
  @(negedge tx);#500;
  if(tx!==0)$fatal(1,"UART_START");
  for(integer n=0;n<8;n=n+1)begin #1000;received[n]=tx;end
  #1000;if(tx!==1)$fatal(1,"UART_STOP");$fwrite(raw,"%c",received);$fflush(raw);uart_bytes=uart_bytes+1;
 end
 function automatic[7:0] expected_pattern(input integer mode,x,y_page,input[31:0] frame);
  reg[7:0] value;integer y;begin
   value=0;
   for(integer b=0;b<8;b=b+1)begin
    y=y_page*8+b;
    case(mode)
     0:value[b]=0;1:value[b]=1;
     2:value[b]=((x/8)+(y/8))%2;
     3:value[b]=((x%2)==0)?(b%2==0):(b%2==1);
     4:value[b]=(x/4)%2;
     5:value[b]=(b<4);
     6:value[b]=(x==0||x==127||y==0||y==63||x==2*y||x==127-2*y);
     7:value[b]=(x==(frame%128)||y==(frame%64));
    endcase
   end
   expected_pattern=value;
  end
 endfunction
 function automatic[7:0] digit(input bit one,input integer column);
  reg[39:0] font;begin font=one?40'h00427f4000:40'h3e5149453e;digit=font[(4-column)*8+:8];end
 endfunction
 always @(posedge dut.frame_done)begin
  #1;
  if(!display_on)$fatal(1,"PANEL_NOT_ON");
  if(panel.seg_remap!==0||panel.com_reverse!==0)$fatal(1,"ROTATION_180_COMMANDS");
  if(dut.snap_inverse!=previous_inverse)expected_inverse_commands=expected_inverse_commands+1;
  if(panel.inverse_commands!=expected_inverse_commands)$fatal(1,"REDUNDANT_OR_MISSING_INVERSE_COMMAND");
  previous_inverse=dut.snap_inverse;
  if(dut.snap_mode<8)begin
   for(integer p=0;p<8;p=p+1)for(integer x=0;x<128;x=x+1)begin
    expected=expected_pattern(dut.snap_mode,x,p,dut.snap_frames);
    if(panel.ram[p*128+x]!==expected)$fatal(1,"FRAME_DATA mode=%d p=%d x=%d expected=%h got=%h",dut.snap_mode,p,x,expected,panel.ram[p*128+x]);
   end
   selftest_checked=selftest_checked+1;
  end else begin
   for(integer k=0;k<9;k=k+1)begin:check_labels
    integer p,c;
    if(k<6)begin p=3+k/3;c=3+(k%3)*5;end
    else if(k<8)begin p=5;c=3+(k-6)*5;end
    else begin p=5;c=12;end
    for(integer col=0;col<5;col=col+1)
     if(panel.ram[p*128+c*8+col]!==digit(dut.snap_keys[k],col))$fatal(1,"KEY_LABEL k=%d snapshot=%h byte=%h",k,dut.snap_keys,panel.ram[p*128+c*8+col]);
   end
   live_checked=live_checked+1;
  end
  if(inverse!==(dut.snap_mode==3||(dut.snap_mode==8&&dut.snap_inverse)))$fatal(1,"INVERSE_COMMAND");
  frames_checked=frames_checked+1;
  if(dut.snap_mode==8&&dut.snap_keys==9'h1ff)$writememh({outdir,"/all_keys_frame.memh"},panel.ram);
 end
 task wait_display(input[8:0] mask);
  begin
   do begin @(posedge dut.frame_done);#2;end while(dut.snap_mode!=8||dut.snap_keys!=mask);
  end
 endtask
 initial begin
  wait(dut.oled_ready);wait(dut.mode==8);wait(dut.patterns_seen==8'hff);
  if(selftest_checked!=8)$fatal(1,"SELFTEST_COVERAGE %d",selftest_checked);
  wait_display(0);
  // Reject a short bounce. Normalized inputs remain active-low at physical pins.
  pins[0]=0;repeat(3)@(negedge clk);pins[0]=1;repeat(24)@(negedge clk);
  if(dut.keys_pressed!=0||led_n!=8'hff||dut.event_total!=0)$fatal(1,"BOUNCE_REJECT");
  for(integer k=0;k<9;k=k+1)begin
   pins[k]=0;repeat(24)@(negedge clk);
   if(dut.keys_pressed!=(9'b1<<k)||led_n!==~(8'(9'b1<<k)))$fatal(1,"KEY_LED_MAPPING k=%d",k);
   wait_display(9'b1<<k);
   if(dut.press_count[k]!=1)$fatal(1,"PRESS_COUNT");
   pins[k]=1;repeat(24)@(negedge clk);wait_display(0);
  end
  // Per-bit debounce independence: KEY1 bounces while stable KEY2/5 qualify.
  pins[2]=0;pins[5]=0;
  repeat(8)begin pins[1]=0;repeat(2)@(negedge clk);pins[1]=1;repeat(2)@(negedge clk);end
  if(dut.keys_pressed!=9'h024)$fatal(1,"FILTERS_NOT_INDEPENDENT");
  wait_display(9'h024);
  pins=0;repeat(24)@(negedge clk);wait_display(9'h1ff);
  if(led_n!==0)$fatal(1,"MULTIKEY_LED");
  pins=9'h1ff;repeat(24)@(negedge clk);wait_display(0);
  rx=0;repeat(10)@(negedge clk);rx=1;repeat(10)@(negedge clk);
  if(!dut.rx_seen)$fatal(1,"RX_ACTIVITY");
  // Hold RST_N long enough; on release the physical driver must replay full frames.
  pins[8]=0;repeat(200100)@(negedge clk);pins[8]=1;
  wait(dut.mode==0);wait(dut.mode==8);wait(dut.patterns_seen==8'hff);
  if(selftest_checked<16)$fatal(1,"SELFTEST_REPLAY");
  repeat(180000)@(negedge clk);
  if(dut.event_total!=38)$fatal(1,"EXACT_EVENT_COUNT");
  for(integer k=0;k<9;k=k+1)if(dut.press_count[k]!=(k==8?3:2))$fatal(1,"EXACT_FINAL_PRESS_COUNT");
  if(dut.seen_keys!=9'h1ff||uart_bytes<296)$fatal(1,"FINAL_COVERAGE");
  wait(!dut.reporter.sending&&dut.reporter.uart_ready&&!dut.reporter.dirty);#100;
  $fclose(raw);
  $display("OLED_KEYS_SIM_PASS frames=%0d live=%0d patterns=%0d uart_bytes=%0d all_keys=1 debounce=1 replay=1",frames_checked,live_checked,selftest_checked,uart_bytes);
  $finish;
 end
 initial begin #300000000;$fatal(1,"OLED_KEYS_TIMEOUT");end
endmodule
