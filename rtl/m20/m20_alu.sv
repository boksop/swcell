`default_nettype none
// Four-bit combinational ALU. Extended carry wires are not an eight-bit ALU.
module m20_alu (
    input  wire [5:0] op,
    input  wire [3:0] a,
    input  wire [3:0] operand,
    input  wire c_in,
    output logic [3:0] result,
    output logic z_out,
    output logic c_out,
    output logic a_we,
    output logic z_we,
    output logic c_we
);
    import m20_pkg::*;
    logic [4:0] extended;
    logic [4:0] subtract_rhs;
    always_comb begin
        result = a;
        c_out = c_in;
        a_we = 1'b0;
        z_we = 1'b0;
        c_we = 1'b0;
        extended = 5'd0;
        subtract_rhs = 5'd0;
        case (op)
            OP_LOAD: begin
                result = operand;
                a_we = 1'b1; z_we = 1'b1;
            end
            OP_ADD, OP_ADC: begin
                extended = {1'b0, a} + {1'b0, operand} +
                           ((op == OP_ADC && c_in) ? 5'd1 : 5'd0);
                result = extended[3:0];
                c_out = extended[4];
                a_we = 1'b1; z_we = 1'b1; c_we = 1'b1;
            end
            OP_SUB, OP_SBC, OP_CMP: begin
                subtract_rhs = {1'b0, operand} +
                               ((op == OP_SBC && !c_in) ? 5'd1 : 5'd0);
                extended = {1'b0, a} - subtract_rhs;
                result = extended[3:0];
                c_out = ({1'b0, a} >= subtract_rhs);
                a_we = (op != OP_CMP); z_we = 1'b1; c_we = 1'b1;
            end
            OP_AND: begin result = a & operand; a_we = 1'b1; z_we = 1'b1; end
            OP_XOR: begin result = a ^ operand; a_we = 1'b1; z_we = 1'b1; end
            OP_OR:  begin result = a | operand; a_we = 1'b1; z_we = 1'b1; end
            OP_NOT: begin result = ~a; a_we = 1'b1; z_we = 1'b1; end
            OP_SHL: begin
                result = {a[2:0], 1'b0}; c_out = a[3];
                a_we = 1'b1; z_we = 1'b1; c_we = 1'b1;
            end
            OP_SHR: begin
                result = {1'b0, a[3:1]}; c_out = a[0];
                a_we = 1'b1; z_we = 1'b1; c_we = 1'b1;
            end
            // These instructions change A without changing either flag.
            OP_MOVA_ARL, OP_MOVA_ARH, OP_IN0, OP_IN1: begin
                result = operand; a_we = 1'b1;
            end
            default: begin end
        endcase
        z_out = (result == 4'h0);
    end
endmodule
`default_nettype wire
