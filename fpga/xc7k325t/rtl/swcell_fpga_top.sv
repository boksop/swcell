`default_nettype none
module swcell_fpga_top #(
 parameter integer CLK_HZ=50_000_000, UART_BAUD=115200,
 parameter integer POR_CYCLES=CLK_HZ/10,
 parameter integer STEP_NS=500, SETTLE_NS=200, SYNC_STAGES=2,
 parameter integer PATTERN_STEPS=32, RANDOM_STEPS=1024
)(input wire sys_clk,
 output wire UART_TX, input wire UART_RXD,
 output wire M11_DL_D, M11_DL_EN, input wire M11_DL_Q,
 output wire M11_DFF_D, M11_DFF_CLK, input wire M11_DFF_Q, M11_DFF_QM,
 output wire LED_G, LED_Y, LED_R);
 wire rst;
 wire suite_done, suite_pass;
 swc_power_on_reset #(.HOLD_CYCLES(POR_CYCLES)) power_on_reset(.clk(sys_clk),.rst(rst));
 assign LED_G=!rst && suite_done && suite_pass;
 assign LED_Y=!rst && !suite_done;
 assign LED_R=!rst && suite_done && !suite_pass;
 // UART_RXD is reserved for a future command interface; Phase 1 is TX-only.
 m11_test_top #(.CLK_HZ(CLK_HZ),.UART_BAUD(UART_BAUD),.STEP_NS(STEP_NS),
   .SETTLE_NS(SETTLE_NS),.SYNC_STAGES(SYNC_STAGES),
   .PATTERN_STEPS(PATTERN_STEPS),.RANDOM_STEPS(RANDOM_STEPS)) engine(
   .clk(sys_clk),.rst(rst),.uart_tx(UART_TX),
   .m11_dl_d(M11_DL_D),.m11_dl_en(M11_DL_EN),.m11_dl_q(M11_DL_Q),
   .m11_dff_d(M11_DFF_D),.m11_dff_clk(M11_DFF_CLK),
   .m11_dff_q(M11_DFF_Q),.m11_dff_qm(M11_DFF_QM),
   .suite_done(suite_done),.suite_pass(suite_pass));
endmodule
`default_nettype wire
