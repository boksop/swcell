`default_nettype none
// Request payload is snapshotted once. Byte handshake tolerates arbitrary UART stalls.
module swc_json_reporter #(parameter [23:0] MODULE_NAME="M11")(
 input wire clk, rst, request_valid, output wire request_ready,
 input wire [1:0] event_type, input wire [23:0] test_name,
 input wire passed,
 input wire [63:0] total_checks, error_checks, q_errors, qm_errors,
 input wire [63:0] first_cycle, first_check, tests, failed_tests,
 input wire [3:0] first_inputs,
 input wire [2:0] first_actual, first_expected, first_mask,
 output wire tx_valid, input wire tx_ready, output reg [7:0] tx_data
);
 function automatic [7:0] hex4(input [3:0] n);
   hex4=(n<10)?(8'd48+{4'b0,n}):(8'd97+{4'b0,n}-8'd10);
 endfunction
 function automatic [127:0] hex64(input [63:0] v);
   integer i;
   begin for(i=0;i<16;i=i+1) hex64[(15-i)*8+:8]=hex4(v[(15-i)*4+:4]);end
 endfunction
 reg active;
 reg [1:0] event_q;
 reg [23:0] name_q;
 reg passed_q;
 reg [63:0] total_q, errors_q, qerr_q, qmerr_q, cycle_q, check_q, tests_q, failed_q;
 reg [3:0] inputs_q;
 reg [2:0] actual_q, expected_q, mask_q;
 reg [8:0] index;
 integer length;
 localparam integer START_LEN=50;
 wire [8*START_LEN-1:0] start_line={"{\"type\":\"TEST_START\",\"module\":\"",MODULE_NAME,"\",\"test\":\"",name_q,"\"}\n"};
 localparam integer RESULT_LEN=204;
 wire [8*RESULT_LEN-1:0] result_line={"{\"type\":\"TEST_RESULT\",\"module\":\"",MODULE_NAME,"\",\"test\":\"",name_q,"\",\"total_checks\":\"0x",hex64(total_q),"\",\"error_checks\":\"0x",hex64(errors_q),"\",\"q_errors\":\"0x",hex64(qerr_q),"\",\"qm_errors\":\"0x",hex64(qmerr_q),"\",\"status\":\"",(passed_q ? "PASS" : "FAIL"),"\"}\n"};
 localparam integer ERROR_LEN=169;
 wire [8*ERROR_LEN-1:0] error_line={"{\"type\":\"FIRST_ERROR\",\"module\":\"",MODULE_NAME,"\",\"test\":\"",name_q,"\",\"cycle\":\"0x",hex64(cycle_q),"\",\"check\":\"0x",hex64(check_q),"\",\"inputs\":\"0x",hex4(inputs_q),"\",\"actual\":\"0x",hex4({1'b0,actual_q}),"\",\"expected\":\"0x",hex4({1'b0,expected_q}),"\",\"mask\":\"0x",hex4({1'b0,mask_q}),"\"}\n"};
 localparam integer COMPLETE_LEN=121;
 wire [8*COMPLETE_LEN-1:0] complete_line={"{\"type\":\"TEST_COMPLETE\",\"module\":\"",MODULE_NAME,"\",\"tests\":\"0x",hex64(tests_q),"\",\"failed_tests\":\"0x",hex64(failed_q),"\",\"status\":\"",(passed_q ? "PASS" : "FAIL"),"\"}\n"};
 assign request_ready=!active;
 assign tx_valid=active;
 always @* begin
   length=0; tx_data=8'h0a;
   case(event_q)
   2'd0:begin length=START_LEN; tx_data=start_line[( START_LEN-1-int'(index))*8 +: 8];end
   2'd1:begin length=RESULT_LEN; tx_data=result_line[( RESULT_LEN-1-int'(index))*8 +: 8];end
   2'd2:begin length=ERROR_LEN; tx_data=error_line[( ERROR_LEN-1-int'(index))*8 +: 8];end
   2'd3:begin length=COMPLETE_LEN; tx_data=complete_line[( COMPLETE_LEN-1-int'(index))*8 +: 8];end
   endcase
 end
 always @(posedge clk) begin
   if(rst) begin
     active<=0;event_q<=0;index<=0;name_q<=0;passed_q<=0;
     total_q<=0;errors_q<=0;qerr_q<=0;qmerr_q<=0;cycle_q<=0;check_q<=0;
     tests_q<=0;failed_q<=0;inputs_q<=0;actual_q<=0;expected_q<=0;mask_q<=0;
   end else if(!active) begin
     if(request_valid) begin
       active<=1;index<=0;event_q<=event_type;
       name_q<=test_name;
       passed_q<=passed;total_q<=total_checks;errors_q<=error_checks;
       qerr_q<=q_errors;qmerr_q<=qm_errors;cycle_q<=first_cycle;check_q<=first_check;
       tests_q<=tests;failed_q<=failed_tests;inputs_q<=first_inputs;
       actual_q<=first_actual;expected_q<=first_expected;mask_q<=first_mask;
     end
   end else if(tx_ready) begin
     if(int'(index)==length-1) begin active<=0;index<=0;end
     else index<=index+1'b1;
   end
 end
endmodule
`default_nettype wire
