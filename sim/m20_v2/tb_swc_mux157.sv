`timescale 1ns/1ps
module tb_swc_mux157;
    logic S,I0,I1;
    wire Y;
    integer vector;
    swc_mux157 dut(.S(S),.I0(I0),.I1(I1),.Y(Y));
    initial begin
        for(vector=0;vector<8;vector=vector+1) begin
            {S,I0,I1}=vector[2:0];#1ps;
            if(Y !== (S?I1:I0)) $fatal(1,"MUX truth table vector=%b actual=%b",vector[2:0],Y);
        end
        $display("SWC_MUX157_PASS vectors=8");
        $finish;
    end
endmodule
