`default_nettype none
module m11_test_top #(
 parameter integer CLK_HZ=100_000_000, UART_BAUD=115200,
 parameter integer STEP_NS=500, SETTLE_NS=200, SYNC_STAGES=2,
 parameter integer PATTERN_STEPS=32, RANDOM_STEPS=1024
)(input wire clk, rst,
 output reg m11_dl_d, m11_dl_en, m11_dff_d, m11_dff_clk,
 input wire m11_dl_q, m11_dff_q, m11_dff_qm,
 output wire uart_tx, output wire suite_done, suite_pass);
 // 64-bit arithmetic avoids overflow in Hz*ns before ceiling conversion.
 localparam integer STEP_CYCLES=int'((64'd1*CLK_HZ*STEP_NS+999_999_999)/1_000_000_000);
 localparam integer SETTLE_CYCLES=int'((64'd1*CLK_HZ*SETTLE_NS+999_999_999)/1_000_000_000);
 localparam BOOT=0, PREP=1, START_SEND=2, START_WAIT=3, GO=4, RUN=5,
   ERR_SEND=6, ERR_WAIT=7, RES_SEND=8, RES_WAIT=9, NEXT_TEST=10,
   COMPLETE_SEND=11, COMPLETE_WAIT=12, FINISHED=13, INIT_WAIT=14;
 reg [3:0] state;
 reg boot_phase;
 reg [7:0] current_test;
 reg [63:0] cycles, tests_done, failed_tests;
 wire is_dff=current_test[4];
 wire l_valid,l_d,l_en,l_check,l_done;
 wire f_valid,f_d,f_clk,f_check,f_done;
 wire step_ready,step_done;
 wire step_valid=(state==BOOT) || ((state==RUN) && (is_dff?f_valid:l_valid));
 wire apply=step_valid && step_ready;
 wire [3:0] stimulus={m11_dff_clk,m11_dff_d,m11_dl_en,m11_dl_d};
 wire [3:0] next_stimulus=(state==BOOT)?{boot_phase,1'b0,1'b1,1'b0}:
                              is_dff?{f_clk,f_d,m11_dl_en,m11_dl_d}:
                                             {m11_dff_clk,m11_dff_d,l_en,l_d};
 reg check_pending;
 wire check_valid=step_done && check_pending && state==RUN;
 wire [2:0] actual, expected, mismatch;
 wire [2:0] mask=is_dff?3'b110:3'b001;
 swc_input_sync #(.WIDTH(3),.STAGES(SYNC_STAGES)) inputs_sync(
   .clk(clk),.rst(rst),.async_in({m11_dff_qm,m11_dff_q,m11_dl_q}),.sync_out(actual));
 swc_step_timer #(.STEP_CYCLES(STEP_CYCLES)) timer(
   .clk(clk),.rst(rst),.valid(step_valid),.ready(step_ready),.done(step_done));
 m11_latch_tester #(.PATTERN_STEPS(PATTERN_STEPS),.RANDOM_STEPS(RANDOM_STEPS)) latch_tester(
   .clk(clk),.rst(rst),.start(state==GO && !is_dff),.test_id(current_test),
   .step_valid(l_valid),.step_ready(step_ready && state==RUN && !is_dff),
   .step_done(step_done && state==RUN && !is_dff),
   .dl_d(l_d),.dl_en(l_en),.check_enable(l_check),.done(l_done));
 m11_dff_tester #(.PATTERN_BITS(PATTERN_STEPS),.RANDOM_BITS(RANDOM_STEPS)) dff_tester(
   .clk(clk),.rst(rst),.start(state==GO && is_dff),.test_id(current_test),
   .step_valid(f_valid),.step_ready(step_ready && state==RUN && is_dff),
   .step_done(step_done && state==RUN && is_dff),
   .dff_d(f_d),.dff_clk(f_clk),.check_enable(f_check),.done(f_done));
 m11_reference_model reference_model(.clk(clk),.rst(rst),.apply(apply),
   .dl_d(next_stimulus[0]),.dl_en(next_stimulus[1]),
   .dff_d(next_stimulus[2]),.dff_clk(next_stimulus[3]),.expected(expected));
 swc_comparator comparator(.actual(actual),.expected(expected),.mask(mask),.mismatch(mismatch));
 wire [7:0] logged_test;
 wire [63:0] total_checks,error_checks,q_errors,qm_errors,first_cycle,first_check;
 wire first_valid,passed;
 wire [3:0] first_inputs;
 wire [2:0] first_actual,first_expected,first_mask;
 swc_test_logger logger(.clk(clk),.rst(rst),.clear(state==PREP),.check_valid(check_valid),
   .test_id_in(current_test),.cycle_number(cycles),.inputs_snapshot(stimulus),
   .actual(actual),.expected(expected),.compare_mask(mask),.mismatch(mismatch),
   .test_id(logged_test),.total_checks(total_checks),.error_checks(error_checks),
   .q_errors(q_errors),.qm_errors(qm_errors),.first_valid(first_valid),
   .first_cycle(first_cycle),.first_check(first_check),.first_inputs(first_inputs),
   .first_actual(first_actual),.first_expected(first_expected),.first_mask(first_mask),.passed(passed));
 wire message_ready;
 wire message_valid=state==START_SEND || state==ERR_SEND || state==RES_SEND || state==COMPLETE_SEND;
 wire [1:0] event_type=(state==START_SEND)?2'd0:(state==ERR_SEND)?2'd2:
                               (state==RES_SEND)?2'd1:2'd3;
 wire byte_valid,byte_ready;
 wire [7:0] byte_data;
 swc_json_reporter reporter(.clk(clk),.rst(rst),.request_valid(message_valid),
   .request_ready(message_ready),.event_type(event_type),
   .test_name({(logged_test[4]?8'h46:8'h4c),8'h30,(8'h30+{4'b0,logged_test[3:0]})}),
   .passed(state==COMPLETE_SEND?(failed_tests==0):passed),
   .total_checks(total_checks),.error_checks(error_checks),.q_errors(q_errors),.qm_errors(qm_errors),
   .first_cycle(first_cycle),.first_check(first_check),.tests(tests_done),.failed_tests(failed_tests),
   .first_inputs(first_inputs),.first_actual(first_actual),.first_expected(first_expected),.first_mask(first_mask),
   .tx_valid(byte_valid),.tx_ready(byte_ready),.tx_data(byte_data));
 swc_uart_tx #(.CLK_HZ(CLK_HZ),.BAUD(UART_BAUD)) uart(
   .clk(clk),.rst(rst),.data(byte_data),.valid(byte_valid),.ready(byte_ready),.tx(uart_tx));
 // Wait for the UART stop bit as well as the final JSON byte acceptance.
 assign suite_done=state==FINISHED;
 assign suite_pass=(failed_tests==0) && suite_done;
 always @(posedge clk) begin
   if(rst) begin
     state<=BOOT; boot_phase<=0; current_test<=8'h01; cycles<=0;tests_done<=0;failed_tests<=0;
     m11_dl_d<=0;m11_dl_en<=0;m11_dff_d<=0;m11_dff_clk<=0;check_pending<=0;
   end else begin
     cycles<=cycles+1'b1;
     if(apply) begin
       {m11_dff_clk,m11_dff_d,m11_dl_en,m11_dl_d}<=next_stimulus;
       check_pending<=(state==BOOT)?1'b0:(is_dff?f_check:l_check);
     end
     case(state)
       BOOT:if(apply) state<=INIT_WAIT;
       INIT_WAIT:if(step_done) begin
         if(!boot_phase) begin boot_phase<=1;state<=BOOT;end
         else state<=PREP;
       end
       PREP:state<=START_SEND;
       START_SEND:if(message_ready) state<=START_WAIT;
       START_WAIT:if(message_ready && byte_ready) state<=GO;
       GO:state<=RUN;
       RUN:if(is_dff?f_done:l_done) state<=first_valid?ERR_SEND:RES_SEND;
       ERR_SEND:if(message_ready) state<=ERR_WAIT;
       ERR_WAIT:if(message_ready && byte_ready) state<=RES_SEND;
       RES_SEND:if(message_ready) state<=RES_WAIT;
       RES_WAIT:if(message_ready && byte_ready) begin
         tests_done<=tests_done+1'b1;
         if(!passed) failed_tests<=failed_tests+1'b1;
         state<=NEXT_TEST;
       end
       NEXT_TEST:begin
         if(current_test==8'h19) state<=COMPLETE_SEND;
         else begin
           current_test<=(current_test==8'h08)?8'h11:current_test+1'b1;
           state<=PREP;
         end
       end
       COMPLETE_SEND:if(message_ready) state<=COMPLETE_WAIT;
       COMPLETE_WAIT:if(message_ready && byte_ready) state<=FINISHED;
       FINISHED:state<=FINISHED;
       default:state<=BOOT;
     endcase
   end
 end
 // Static configuration guards are also checked by build.tcl before synthesis.
 // synthesis translate_off
 initial begin
   if(CLK_HZ<=0 || UART_BAUD<=0 || (CLK_HZ+UART_BAUD/2)/UART_BAUD<2)
     $fatal(1,"Invalid clock / UART configuration");
   if(STEP_NS<500 || SETTLE_NS<200 || SYNC_STAGES<2 ||
      STEP_CYCLES<SETTLE_CYCLES+SYNC_STAGES+2)
     $fatal(1,"Step must include physical settling plus CDC pipeline and comparison margin");
   if(PATTERN_STEPS<8 || RANDOM_STEPS<1) $fatal(1,"Invalid test iteration counts");
 end
 // synthesis translate_on
endmodule
`default_nettype wire
