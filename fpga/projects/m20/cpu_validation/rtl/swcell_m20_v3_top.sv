`default_nettype none
module swcell_m20_v3_top #(
 parameter STORAGE_MODE="FUNCTIONAL_STORAGE",
 parameter PONG_FILE="",SNAKE_FILE="",
 parameter [11:0] SNAKE_TICK_DONE=m20_v3_game_pkg::SNAKE_DONE,
 parameter integer CLK_HZ=50000000,UART_BAUD=115200,
 POR_CYCLES=5000000,DEBOUNCE_CYCLES=1000000,REPORT_CYCLES=50000000,
 OLED_RESET_CYCLES=500000,OLED_RELEASE_CYCLES=500000,OLED_ON_WAIT_CYCLES=5000000,
 PONG_HZ=10,SNAKE_HZ=5
)(input wire sys_clk,RST_N,KEY0,KEY1,KEY2,KEY3,KEY4,KEY5,KEY6,KEY7,UART_RXD,
 output wire OLED_RST_N,OLED_DC,OLED_SCK,OLED_MOSI,OLED_CS_N,
 output wire LED0,LED1,LED2,LED3,LED4,LED5,LED6,LED7,UART_TX);
 wire rst;
 swc_power_on_reset #(.HOLD_CYCLES(POR_CYCLES)) por(.clk(sys_clk),.rst(rst));
 wire[8:0] buttons,press_pulse,release_pulse;
 swc_debounce #(.WIDTH(9),.STABLE_CYCLES(DEBOUNCE_CYCLES)) filter(
  .clk(sys_clk),.rst(rst),.async_pressed(~{RST_N,KEY7,KEY6,KEY5,KEY4,KEY3,KEY2,KEY1,KEY0}),
  .pressed(buttons),.press_pulse(press_pulse),.release_pulse(release_pulse));
 // Preserve the frozen IN0/IN1 meanings; wiring is the user's physical mapping.
 wire[5:0] raw_keys={buttons[6],buttons[5],buttons[1],buttons[3],buttons[0],buttons[2]};
 wire[5:0] key_press={press_pulse[6],press_pulse[5],press_pulse[1],press_pulse[3],press_pulse[0],press_pulse[2]};
 wire[5:0] keys,consumed_keys;
 wire input_sample_ce,input0_ack,input1_ack;
 wire[3:0] queued_keys;wire[9:0] key_overflows;
 swc_key_event_buffer key_events(.clk(sys_clk),.rst(rst||cpu_reset),.sample_ce(input_sample_ce),
  .read0_ack(input0_ack),.read1_ack(input1_ack),.levels(raw_keys),.press(key_press),.consumed_keys(consumed_keys),
  .keys(keys),.queued(queued_keys),.overflows(key_overflows));
 wire rx;wire[7:0] command;wire command_valid,command_error;
 swc_input_sync #(.WIDTH(1),.STAGES(2)) rx_sync(.clk(sys_clk),.rst(rst),.async_in(UART_RXD),.sync_out(rx));
 swc_uart_rx #(.CLK_HZ(CLK_HZ),.BAUD(UART_BAUD)) receiver(.clk(sys_clk),.rst(rst),.rx(rx),.data(command),.valid(command_valid),.framing_error(command_error));
 wire game,run_requested,active,master_hold,slave_open,commit_ce,cpu_reset;
 wire[11:0] pc;wire[7:0] ar,ram_addr;wire[3:0] accumulator,gpo,ram_wdata,ram_rdata;
 wire z,c,halted,trapped,ram_ce,ram_oe,ram_we,retire_valid;
 wire[2:0] ustate;wire[15:0] instruction,phase,cycle_ticks;
 wire[63:0] microcycles,retired,reads,writes,ticks,errors,frame_ticks;
 wire[1023:0] frame_ram;wire frame_valid,frame_game,frame_pulse;wire[95:0] debug_sample;
 // Before the first game snapshot, A starts the current ROM instead of
 // selecting another one. A stopped reset must not require the pause key.
 wire boot_entry=press_pulse[5]&&!frame_valid;
 wire select_request=(press_pulse[5]&&frame_valid)||(command_valid&&(command=="p"||command=="s"));
 wire select_game=(command_valid&&(command=="p"||command=="s"))?(command=="s"):!game;
 wire reset_request=press_pulse[8]||(!game&&press_pulse[6])||(command_valid&&command=="r");
 // KEY4 is the easy-to-hit center of the direction pad: deliberately unused.
 wire run_toggle=(press_pulse[7]&&frame_valid)||(boot_entry&&!run_requested)||(command_valid&&command==" ");
 wire step_request=command_valid&&command=="n";
 wire speed_request=command_valid&&(command=="1"||command=="2"||command=="3");
 wire[15:0] speed_ticks=command=="1"?16'd500:command=="2"?16'd100:16'd50;
 swc_m20_v3_system #(.CLK_HZ(CLK_HZ),.PONG_FILE(PONG_FILE),.SNAKE_FILE(SNAKE_FILE),
  .PONG_HZ(PONG_HZ),.SNAKE_HZ(SNAKE_HZ),.SNAKE_TICK_DONE(SNAKE_TICK_DONE),.STORAGE_MODE(STORAGE_MODE)) system(
  .clk(sys_clk),.power_reset(rst),.*);
 wire oled_ready;wire[31:0] oled_frames;
 swc_m20_v3_display #(.RESET_CYCLES(OLED_RESET_CYCLES),.RELEASE_CYCLES(OLED_RELEASE_CYCLES),
  .ON_WAIT_CYCLES(OLED_ON_WAIT_CYCLES)) display(.clk(sys_clk),.rst(rst),.game(frame_game),.valid(frame_valid),
  .state_ram(frame_ram),.running(run_requested),.halted(halted),.trapped(trapped),
  .oled_rst_n(OLED_RST_N),.oled_dc(OLED_DC),.oled_cs_n(OLED_CS_N),.oled_sck(OLED_SCK),.oled_mosi(OLED_MOSI),.initialized(oled_ready),.frames(oled_frames));
 assign {LED7,LED6,LED5,LED4,LED3,LED2,LED1,LED0}=~{errors!=0||(|key_overflows),halted||trapped,game,run_requested,gpo};
 logic[7:0] phase_trace=0;
 always_ff @(posedge sys_clk)begin
  if(rst)phase_trace<=0;
  else if(active)case(phase)
   5:phase_trace[1:0]<={master_hold,slave_open};
   22:phase_trace[3:2]<={master_hold,slave_open};
   30:phase_trace[5:4]<={master_hold,slave_open};
   45:phase_trace[7:6]<={master_hold,slave_open};
   default:begin end
  endcase
 end
 // A complete atomic CPU/bus/counter/RAM snapshot, not an FPGA game engine.
 localparam FORMAT="{\"type\":\"M20_V3_STATE\",\"build\":\"M20V3F06\",\"game\":\"#\",\"frame_game\":\"#\",\"frame_valid\":\"#\",\"frame_ticks\":\"################\",\"debug\":\"########################\",\"micro\":\"################\",\"retired\":\"################\",\"reads\":\"################\",\"writes\":\"################\",\"ticks\":\"################\",\"errors\":\"################\",\"oled_frames\":\"########\",\"cycle_ticks\":\"####\",\"phase_trace\":\"##\",\"ram\":\"################################################################################################################################################################################################################################################################\"}\n";
 wire[95:0] report_debug={|key_overflows,queued_keys,key_overflows,debug_sample[80:0]};
 wire[1635:0] payload={3'b0,game,3'b0,frame_game,3'b0,frame_valid,frame_ticks,report_debug,microcycles,retired,reads,writes,ticks,errors,oled_frames,cycle_ticks,phase_trace,frame_ram};
 logic[31:0] report_timer=0;wire uart_ready;
 wire report_request=uart_ready&&report_timer==0&&oled_ready&&!cpu_reset;
 swc_uart_hex_json #(.CLK_HZ(CLK_HZ),.BAUD(UART_BAUD),.HEX_DIGITS(409),.FORMAT(FORMAT)) reporter(
  .clk(sys_clk),.rst(rst),.request(report_request),.payload(payload),.tx(UART_TX),.ready(uart_ready));
 always_ff @(posedge sys_clk)begin
  if(rst)report_timer<=0;
  else if(report_request)report_timer<=32'(REPORT_CYCLES-1);
  else if(report_timer!=0)report_timer<=report_timer-1'b1;
 end
endmodule
`default_nettype wire
