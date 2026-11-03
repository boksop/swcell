`default_nettype none
// Strict combinational decode: every reserved bit is checked. No ignored fields.
module m20_decoder (
    input  wire [15:0] instruction,
    output logic legal,
    output logic is_memory,
    output logic memory_write,
    output logic indirect,
    output logic [5:0] op
);
    import m20_pkg::*;
    always_comb begin
        legal = 1'b0;
        is_memory = 1'b0;
        memory_write = 1'b0;
        indirect = 1'b0;
        op = OP_INVALID;
        case (instruction[15:12])
            4'h0, 4'h1, 4'h2, 4'h3, 4'h4, 4'h5, 4'h6: begin
                if (instruction[11:4] == 8'h00) begin
                    legal = 1'b1;
                    case (instruction[15:12])
                        4'h0: op = OP_LOAD;
                        4'h1: op = OP_ADD;
                        4'h2: op = OP_ADC;
                        4'h3: op = OP_SUB;
                        4'h4: op = OP_SBC;
                        4'h5: op = OP_AND;
                        4'h6: op = OP_XOR;
                        default: op = OP_INVALID;
                    endcase
                end
            end
            4'h7: begin
                if (instruction[7:0] == 8'h00) begin
                    case (instruction[11:8])
                        4'h0: begin legal = 1'b1; op = OP_SHL; end
                        4'h1: begin legal = 1'b1; op = OP_SHR; end
                        4'h2: begin legal = 1'b1; op = OP_NOT; end
                        default: begin end
                    endcase
                end
            end
            4'h8, 4'h9: begin
                if ((instruction[11:8] <= 4'h9) &&
                    ((instruction[15:12] == 4'h8) || (instruction[7:0] == 8'h00))) begin
                    legal = 1'b1;
                    is_memory = 1'b1;
                    indirect = (instruction[15:12] == 4'h9);
                    memory_write = (instruction[11:8] == 4'h1);
                    case (instruction[11:8])
                        4'h0: op = OP_LOAD;
                        4'h1: op = OP_ST;
                        4'h2: op = OP_ADD;
                        4'h3: op = OP_ADC;
                        4'h4: op = OP_SUB;
                        4'h5: op = OP_SBC;
                        4'h6: op = OP_CMP;
                        4'h7: op = OP_AND;
                        4'h8: op = OP_XOR;
                        4'h9: op = OP_OR;
                        default: op = OP_INVALID;
                    endcase
                end
            end
            4'hA: begin
                if (instruction[7:4] == 4'h0) begin
                    case (instruction[11:8])
                        4'h0: begin legal = 1'b1; op = OP_ARL; end
                        4'h1: begin legal = 1'b1; op = OP_ARH; end
                        default: begin
                            if (instruction[3:0] == 4'h0) begin
                                case (instruction[11:8])
                                    4'h2: begin legal = 1'b1; op = OP_MOVARL; end
                                    4'h3: begin legal = 1'b1; op = OP_MOVARH; end
                                    4'h4: begin legal = 1'b1; op = OP_MOVA_ARL; end
                                    4'h5: begin legal = 1'b1; op = OP_MOVA_ARH; end
                                    4'h6: begin legal = 1'b1; op = OP_INCAR; end
                                    default: begin end
                                endcase
                            end
                        end
                    endcase
                end
            end
            4'hB: begin legal = 1'b1; op = OP_JMP; end
            4'hC: begin legal = 1'b1; op = OP_JZ; end
            4'hD: begin legal = 1'b1; op = OP_JC; end
            4'hE: begin
                if (instruction[7:0] == 8'h00) begin
                    case (instruction[11:8])
                        4'h0: begin legal = 1'b1; op = OP_IN0; end
                        4'h1: begin legal = 1'b1; op = OP_IN1; end
                        4'h2: begin legal = 1'b1; op = OP_OUT; end
                        default: begin end
                    endcase
                end
            end
            4'hF: begin
                if (instruction[7:0] == 8'h00) begin
                    case (instruction[11:8])
                        4'h0: begin legal = 1'b1; op = OP_NOP; end
                        4'h1: begin legal = 1'b1; op = OP_HALT; end
                        default: begin end
                    endcase
                end
            end
            default: begin end
        endcase
    end
endmodule
`default_nettype wire
