`default_nettype none
module swcell_oled_keys_top #(
 parameter integer CLK_HZ=50000000,UART_BAUD=115200,POR_CYCLES=5000000,
 DEBOUNCE_CYCLES=1000000,SPI_HIGH_CYCLES=2,SPI_LOW_CYCLES=3,RESET_CYCLES=500000,
 RELEASE_CYCLES=500000,ON_WAIT_CYCLES=5000000,FRAME_GAP_CYCLES=800000,
 PATTERN_FRAMES=60,LONG_HOLD_CYCLES=100000000,REPORT_CYCLES=25000000,
 parameter bit OLED_ROTATE_180=1
)(input wire sys_clk,RST_N,KEY0,KEY1,KEY2,KEY3,KEY4,KEY5,KEY6,KEY7,UART_RXD,
 output wire OLED_RST_N,OLED_DC,OLED_SCK,OLED_MOSI,OLED_CS_N,
 output wire LED0,LED1,LED2,LED3,LED4,LED5,LED6,LED7,UART_TX);
 wire rst;
 swc_power_on_reset #(.HOLD_CYCLES(POR_CYCLES)) por(.clk(sys_clk),.rst(rst));
 wire[8:0] keys_pressed,press_pulse,release_pulse;
 swc_debounce #(.WIDTH(9),.STABLE_CYCLES(DEBOUNCE_CYCLES)) keys_filter(
  .clk(sys_clk),.rst(rst),.async_pressed(~{RST_N,KEY7,KEY6,KEY5,KEY4,KEY3,KEY2,KEY1,KEY0}),
  .pressed(keys_pressed),.press_pulse(press_pulse),.release_pulse(release_pulse));
 assign {LED7,LED6,LED5,LED4,LED3,LED2,LED1,LED0}=~keys_pressed[7:0];
 wire rx_activity;
 swc_input_sync #(.WIDTH(1),.STAGES(2)) rx_watch(.clk(sys_clk),.rst(rst),.async_in(!UART_RXD),.sync_out(rx_activity));
 logic rx_seen,old_ready,report_changed;
 logic[8:0] seen_keys;logic[31:0] event_total,frame_total,seconds,second_count;
 logic[31:0] press_count[0:8];wire[287:0] packed_counts;
 for(genvar p=0;p<9;p=p+1)begin:counts_bus assign packed_counts[p*32+:32]=press_count[p];end
 logic[3:0] mode,last_key;logic last_down,inverse_live;
 logic[7:0] patterns_seen;logic[31:0] mode_frames,gap,long_count;logic long_pending;
 wire frame_ready,frame_done,oled_ready;
 wire frame_start=frame_ready&&gap==0&&!frame_done;
 logic[3:0] snap_mode,snap_last_key;logic snap_last_down,snap_inverse;
 logic[8:0] snap_keys,snap_seen;logic[31:0] snap_events,snap_seconds,snap_frames;
 wire[9:0] pixel_address;wire pixel_req;wire[7:0] pixel_data;
 swc_io_diag_pixels pixels(.address(pixel_address),.mode(snap_mode),.keys(snap_keys),.seen(snap_seen),
  .last_key(snap_last_key),.last_down(snap_last_down),.events(snap_events),.seconds(snap_seconds),.frames(snap_frames),.data(pixel_data));
 swc_ssd1306 #(.SPI_HIGH_CYCLES(SPI_HIGH_CYCLES),.SPI_LOW_CYCLES(SPI_LOW_CYCLES),.RESET_CYCLES(RESET_CYCLES),.RELEASE_CYCLES(RELEASE_CYCLES),.ON_WAIT_CYCLES(ON_WAIT_CYCLES),.ROTATE_180(OLED_ROTATE_180)) oled(
  .clk(sys_clk),.rst(rst),.frame_start(frame_start),.inverse(snap_inverse),.frame_ready(frame_ready),.frame_done(frame_done),.initialized(oled_ready),
  .pixel_addr(pixel_address),.pixel_req(pixel_req),.pixel_valid(1'b1),.pixel_data(pixel_data),
  .oled_rst_n(OLED_RST_N),.oled_dc(OLED_DC),.oled_cs_n(OLED_CS_N),.oled_sck(OLED_SCK),.oled_mosi(OLED_MOSI));
 wire[31:0] merged_updates;
 swc_io_diag_uart #(.CLK_HZ(CLK_HZ),.BAUD(UART_BAUD),.PERIOD_CYCLES(REPORT_CYCLES)) reporter(
  .clk(sys_clk),.rst(rst),.changed(report_changed),.snapshot_stable((press_pulse|release_pulse)==0),
  .keys(keys_pressed),.seen(seen_keys),.events(event_total),.frames(frame_total),.seconds(seconds),
  .counts(packed_counts),.mode(mode),.patterns(patterns_seen),.oled_ready(oled_ready),.rx_seen(rx_seen),.tx(UART_TX),.merged_updates(merged_updates));
 function automatic[3:0] bit_count(input[8:0] value);
  reg[3:0] n;begin n=0;for(integer i=0;i<9;i=i+1)n=n+{3'b0,value[i]};bit_count=n;end
 endfunction
 always_ff @(posedge sys_clk)begin
  if(rst)begin
   rx_seen<=0;old_ready<=0;report_changed<=0;seen_keys<=0;event_total<=0;frame_total<=0;seconds<=0;second_count<=0;
   for(integer i=0;i<9;i=i+1)press_count[i]<=0;
   mode<=0;last_key<=15;last_down<=0;inverse_live<=0;patterns_seen<=0;mode_frames<=0;gap<=0;long_count<=0;long_pending<=0;
   snap_mode<=0;snap_keys<=0;snap_seen<=0;snap_events<=0;snap_seconds<=0;snap_frames<=0;snap_last_key<=15;snap_last_down<=0;snap_inverse<=0;
  end else begin
   old_ready<=oled_ready;
   report_changed<=(|(press_pulse|release_pulse))||(oled_ready&&!old_ready)||(frame_done&&mode<8&&snap_mode==mode&&mode_frames==32'(PATTERN_FRAMES-1));
   if(rx_activity)rx_seen<=1;
   if(second_count==32'(CLK_HZ-1))begin second_count<=0;seconds<=seconds+1'b1;end else second_count<=second_count+1'b1;
   if(gap!=0)gap<=gap-1'b1;
   if(frame_start)begin
    snap_mode<=mode;snap_keys<=keys_pressed;snap_seen<=seen_keys;snap_events<=event_total;snap_seconds<=seconds;snap_frames<=frame_total;
    snap_last_key<=last_key;snap_last_down<=last_down;snap_inverse<=mode==3||(mode==8&&inverse_live);
   end
   if(frame_done)begin
    frame_total<=frame_total+1'b1;gap<=32'(FRAME_GAP_CYCLES);
    if(snap_mode<8&&snap_mode==mode)patterns_seen[snap_mode]<=1;
    if(mode<8&&snap_mode==mode)begin
     if(mode_frames==32'(PATTERN_FRAMES-1))begin mode_frames<=0;mode<=mode+1'b1;end
     else mode_frames<=mode_frames+1'b1;
    end
   end
   seen_keys<=seen_keys|press_pulse;
   if(|(press_pulse|release_pulse))event_total<=event_total+{28'b0,bit_count(press_pulse|release_pulse)};
   for(integer i=0;i<9;i=i+1)begin
    if(press_pulse[i])press_count[i]<=press_count[i]+1'b1;
    if(press_pulse[i]||release_pulse[i])begin last_key<=4'(i);last_down<=press_pulse[i];end
   end
   if(|press_pulse)begin mode<=8;mode_frames<=0;end
   if(press_pulse[8])inverse_live<=!inverse_live;
   if(keys_pressed[8])begin
    if(long_count<32'(LONG_HOLD_CYCLES))long_count<=long_count+1'b1;
    if(long_count==32'(LONG_HOLD_CYCLES-1))long_pending<=1;
   end else begin
    long_count<=0;long_pending<=0;
    if(release_pulse[8]&&long_pending)begin mode<=0;mode_frames<=0;patterns_seen<=0;inverse_live<=0;report_changed<=1;end
   end
  end
 end
endmodule
`default_nettype wire
