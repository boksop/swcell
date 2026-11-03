`timescale 1ns/1ps
module tb_m20_isa;
    import m20_pkg::*;
    logic [15:0] instruction;
    wire legal,is_memory,memory_write,indirect;
    wire [5:0] decoded_op;
    logic [5:0] op;
    logic [3:0] a,operand;
    logic c_in;
    wire [3:0] result;
    wire z_out,c_out,a_we,z_we,c_we;
    integer word_index,operation,ai,bi,ci,accepted,alu_vectors;
    integer value,expected_result,expected_c,expected_awe,expected_zwe,expected_cwe;
    integer sub;
    m20_decoder decoder(.instruction(instruction),.legal(legal),.is_memory(is_memory),
        .memory_write(memory_write),.indirect(indirect),.op(decoded_op));
    m20_alu alu(.op(op),.a(a),.operand(operand),.c_in(c_in),.result(result),
        .z_out(z_out),.c_out(c_out),.a_we(a_we),.z_we(z_we),.c_we(c_we));

    // Independent masks from the frozen bit contract, not decoder RTL tables.
    function automatic bit legal_word(input logic [15:0] w);
        case (w[15:12])
            0,1,2,3,4,5,6: legal_word=(w[11:4]==0);
            7: legal_word=(w==16'h7000 || w==16'h7100 || w==16'h7200);
            8: legal_word=(w[11:8]<=9);
            9: legal_word=(w[11:8]<=9 && w[7:0]==0);
            10: legal_word=((w & 16'hFFF0)==16'hA000 || (w & 16'hFFF0)==16'hA100 ||
                 w==16'hA200 || w==16'hA300 || w==16'hA400 || w==16'hA500 || w==16'hA600);
            11,12,13: legal_word=1;
            14: legal_word=(w==16'hE000 || w==16'hE100 || w==16'hE200);
            15: legal_word=(w==16'hF000 || w==16'hF100);
            default: legal_word=0;
        endcase
    endfunction
    function automatic integer expected_operation(input logic [15:0] w);
        integer s;
        begin
            s=w[11:8];
            case (w[15:12])
                0: expected_operation=0;
                1: expected_operation=1;
                2: expected_operation=2;
                3: expected_operation=3;
                4: expected_operation=4;
                5: expected_operation=6;
                6: expected_operation=7;
                7: case(s) 0:expected_operation=10;1:expected_operation=11;default:expected_operation=9;endcase
                8,9: case(s)
                    0:expected_operation=0;1:expected_operation=12;2:expected_operation=1;
                    3:expected_operation=2;4:expected_operation=3;5:expected_operation=4;
                    6:expected_operation=5;7:expected_operation=6;8:expected_operation=7;
                    default:expected_operation=8;
                endcase
                10: expected_operation=13+s;
                11: expected_operation=20;
                12: expected_operation=21;
                13: expected_operation=22;
                14: expected_operation=23+s;
                default: expected_operation=26+s;
            endcase
        end
    endfunction
    initial begin
        instruction=0;op=0;a=0;operand=0;c_in=0;accepted=0;alu_vectors=0;
        for (word_index=0;word_index<65536;word_index=word_index+1) begin
            instruction=word_index[15:0];#1ps;
            if (legal !== legal_word(instruction))
                $fatal(1,"decode legality word=%h actual=%b",instruction,legal);
            if (legal) begin
                accepted=accepted+1;
                if (decoded_op !== expected_operation(instruction))
                    $fatal(1,"decode operation word=%h actual=%0d expected=%0d",instruction,decoded_op,expected_operation(instruction));
                if (is_memory !== (instruction[15:12]==8 || instruction[15:12]==9))
                    $fatal(1,"decode memory class word=%h",instruction);
                if (memory_write !== (is_memory && instruction[11:8]==1))
                    $fatal(1,"decode store word=%h",instruction);
                if (indirect !== (instruction[15:12]==9))
                    $fatal(1,"decode indirect word=%h",instruction);
            end else if (is_memory || memory_write || indirect || decoded_op!=63)
                $fatal(1,"invalid instruction enabled operation word=%h",instruction);
        end
        if (accepted!=15015) $fatal(1,"legal count %0d",accepted);
        for (operation=0;operation<64;operation=operation+1)
          for (ai=0;ai<16;ai=ai+1)
            for (bi=0;bi<16;bi=bi+1)
              for (ci=0;ci<2;ci=ci+1) begin
                op=operation[5:0];a=ai[3:0];operand=bi[3:0];c_in=ci[0];
                expected_result=ai;expected_c=ci;
                expected_awe=0;expected_zwe=0;expected_cwe=0;
                case(operation)
                    0: begin expected_result=bi;expected_awe=1;expected_zwe=1;end
                    1,2: begin
                        value=ai+bi+(operation==2 ? ci : 0);
                        expected_result=value & 15;expected_c=(value>=16);
                        expected_awe=1;expected_zwe=1;expected_cwe=1;
                    end
                    3,4,5: begin
                        value=ai-bi-(operation==4 ? 1-ci : 0);
                        expected_result=value & 15;expected_c=(value>=0);
                        expected_awe=(operation!=5);expected_zwe=1;expected_cwe=1;
                    end
                    6: begin expected_result=ai & bi;expected_awe=1;expected_zwe=1;end
                    7: begin expected_result=ai ^ bi;expected_awe=1;expected_zwe=1;end
                    8: begin expected_result=ai | bi;expected_awe=1;expected_zwe=1;end
                    9: begin expected_result=ai ^ 15;expected_awe=1;expected_zwe=1;end
                    10: begin expected_result=(ai*2) & 15;expected_c=(ai>=8);expected_awe=1;expected_zwe=1;expected_cwe=1;end
                    11: begin expected_result=ai/2;expected_c=ai%2;expected_awe=1;expected_zwe=1;expected_cwe=1;end
                    17,18,23,24: begin expected_result=bi;expected_awe=1;end
                    default: begin end
                endcase
                #1ps;
                if ({a_we,z_we,c_we} !== {expected_awe[0],expected_zwe[0],expected_cwe[0]} ||
                    result!==expected_result[3:0] || c_out!==expected_c[0] ||
                    z_out!==(expected_result==0))
                    $fatal(1,"ALU op=%0d A=%0d R=%0d C=%0d actual=%h/%b/%b we=%b%b%b expected=%h/%b",operation,ai,bi,ci,result,z_out,c_out,a_we,z_we,c_we,expected_result[3:0],expected_c[0]);
                alu_vectors=alu_vectors+1;
              end
        $display("M20_ISA_PASS words=65536 legal=%0d illegal=%0d alu_vectors=%0d",accepted,65536-accepted,alu_vectors);
        $finish;
    end
endmodule
