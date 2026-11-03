`default_nettype none
module swc_test_logger #(
 parameter integer INPUT_WIDTH=4, OUTPUT_WIDTH=3,
 parameter [OUTPUT_WIDTH-1:0] Q_MASK=3'b011, QM_MASK=3'b100
)(
 input wire clk, rst, clear, check_valid,
 input wire [7:0] test_id_in,
 input wire [63:0] cycle_number,
 input wire [INPUT_WIDTH-1:0] inputs_snapshot,
 input wire [OUTPUT_WIDTH-1:0] actual, expected, compare_mask, mismatch,
 output reg [7:0] test_id,
 output reg [63:0] total_checks, error_checks, q_errors, qm_errors,
 output reg first_valid,
 output reg [63:0] first_cycle, first_check,
 output reg [INPUT_WIDTH-1:0] first_inputs,
 output reg [OUTPUT_WIDTH-1:0] first_actual, first_expected, first_mask,
 output wire passed
);
 wire q_bad=|(mismatch & Q_MASK);
 wire qm_bad=|(mismatch & QM_MASK);
 wire any_bad=|mismatch;
 assign passed=(error_checks==0);
 always @(posedge clk) begin
   if(rst || clear) begin
     test_id<=rst?0:test_id_in;
     total_checks<=0; error_checks<=0; q_errors<=0; qm_errors<=0;
     first_valid<=0; first_cycle<=0; first_check<=0;
     first_inputs<=0; first_actual<=0; first_expected<=0; first_mask<=0;
   end else if(check_valid) begin
     total_checks<=total_checks+1'b1;
     if(q_bad) q_errors<=q_errors+1'b1;
     if(qm_bad) qm_errors<=qm_errors+1'b1;
     if(any_bad) begin
       error_checks<=error_checks+1'b1;
       if(!first_valid) begin
         first_valid<=1;
         first_cycle<=cycle_number; first_check<=total_checks+1'b1;
         first_inputs<=inputs_snapshot;
         first_actual<=actual; first_expected<=expected; first_mask<=compare_mask;
       end
     end
   end
 end
endmodule
`default_nettype wire
