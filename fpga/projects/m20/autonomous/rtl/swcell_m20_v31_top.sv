`default_nettype none
// Application-independent board platform. Only CPU OUT can drive the OLED bus.
module swcell_m20_v31_top #(
 parameter ROM_FILE="",parameter integer CLK_HZ=50000000,UART_BAUD=115200,
 POR_CYCLES=5000000,OLED_RESET_CYCLES=500000,OLED_RELEASE_CYCLES=500000,
 DEBUG_DEBOUNCE_CYCLES=1000000,REPORT_CYCLES=50000000
)(input wire sys_clk,RST_N,KEY0,KEY1,KEY2,KEY3,KEY4,KEY5,KEY6,KEY7,UART_RXD,
 output wire OLED_RST_N,OLED_DC,OLED_SCK,OLED_MOSI,OLED_CS_N,
 output wire LED0,LED1,LED2,LED3,LED4,LED5,LED6,LED7,UART_TX);
 wire rst;
 swc_power_on_reset #(.HOLD_CYCLES(POR_CYCLES)) por(.clk(sys_clk),.rst(rst));
 // This independent power-up sequence is never restarted by CPU/game reset.
 logic[31:0] oled_timer=0;logic oled_ready=0;
 assign OLED_RST_N=!rst&&oled_timer>=OLED_RESET_CYCLES;
 always_ff @(posedge sys_clk)begin
  if(rst)begin oled_timer<=0;oled_ready<=0;end
  else if(!oled_ready)begin
   if(oled_timer==OLED_RESET_CYCLES+OLED_RELEASE_CYCLES-1)oled_ready<=1;
   else oled_timer<=oled_timer+1'b1;
  end
 end
 wire[5:0] keys;wire[3:0] gpo;
 swc_m20_v31_gpio gpio(.clk(sys_clk),.power_reset(rst),.KEY0(KEY0),.KEY1(KEY1),.KEY2(KEY2),.KEY3(KEY3),
  .KEY5(KEY5),.KEY6(KEY6),.gpo(gpo),.keys(keys),
  .oled_cs_n(OLED_CS_N),.oled_dc(OLED_DC),.oled_sck(OLED_SCK),.oled_mosi(OLED_MOSI));
 wire reset_level;
 swc_input_sync #(.WIDTH(1)) reset_sync(.clk(sys_clk),.rst(rst),.async_in(!RST_N),.sync_out(reset_level));
 wire debug_pressed,debug_press,debug_release;
 // Debouncing ONLY the FPGA debug pause key; not in the six CPU inputs.
 swc_debounce #(.WIDTH(1),.STABLE_CYCLES(DEBUG_DEBOUNCE_CYCLES)) debug_key(
  .clk(sys_clk),.rst(rst),.async_pressed(!KEY7),.pressed(debug_pressed),.press_pulse(debug_press),.release_pulse(debug_release));
 wire rx;wire[7:0] command;wire command_valid,command_error;
 swc_input_sync #(.WIDTH(1)) rx_sync(.clk(sys_clk),.rst(rst),.async_in(UART_RXD),.sync_out(rx));
 swc_uart_rx #(.CLK_HZ(CLK_HZ),.BAUD(UART_BAUD)) receiver(
  .clk(sys_clk),.rst(rst),.rx(rx),.data(command),.valid(command_valid),.framing_error(command_error));
 wire power_reset=rst;
 wire start_enable=oled_ready;
 wire reset_request=reset_level||(command_valid&&command=="r");
 wire run_toggle=debug_press||(command_valid&&command==" ");
 wire step_request=command_valid&&command=="n";
 wire active,run_requested,cpu_reset,master_hold,slave_open,commit_ce;
 wire[11:0] pc,held_pc;wire[7:0] ar,ram_addr;wire[3:0] accumulator,ram_wdata,ram_rdata;
 wire z,c,halted,trapped,ram_ce,ram_oe,ram_we,retire_valid,write_commit,read_commit,held_retire;
 wire[2:0] ustate;wire[15:0] instruction,phase,held_word;
 wire[63:0] microcycles,retired,reads,writes,errors;
 swc_m20_v31_service #(.ROM_FILE(ROM_FILE)) service(.clk(sys_clk),.*);
 assign {LED7,LED6,LED5,LED4,LED3,LED2,LED1,LED0}=~{errors!=0,halted||trapped,active,run_requested,gpo};
 // Generic diagnostics: no game ID, RAM schema, frame timer or framebuffer.
 localparam FORMAT="{\"type\":\"M20_V31_STATE\",\"build\":\"M20V31A01\",\"pc\":\"###\",\"ar\":\"##\",\"a\":\"#\",\"gpo\":\"#\",\"ustate\":\"#\",\"keys\":\"##\",\"flags\":\"##\",\"micro\":\"################\",\"retired\":\"################\",\"reads\":\"################\",\"writes\":\"################\",\"errors\":\"################\"}\n";
 wire[367:0] payload={pc,ar,accumulator,gpo,1'b0,ustate,2'b0,keys,1'b0,active,run_requested,cpu_reset,halted,trapped,z,c,microcycles,retired,reads,writes,errors};
 logic[31:0] report_timer=0;wire uart_ready;
 wire report_request=uart_ready&&report_timer==0&&!cpu_reset;
 swc_uart_hex_json #(.CLK_HZ(CLK_HZ),.BAUD(UART_BAUD),.HEX_DIGITS(92),.FORMAT(FORMAT)) reporter(
  .clk(sys_clk),.rst(rst),.request(report_request),.payload(payload),.tx(UART_TX),.ready(uart_ready));
 always_ff @(posedge sys_clk)begin
  if(rst)report_timer<=0;
  else if(report_request)report_timer<=REPORT_CYCLES-1;
  else if(report_timer!=0)report_timer<=report_timer-1'b1;
 end
endmodule
`default_nettype wire
