`timescale 1ns/1ps
// Simulation memory only. Mapping metadata is not a CPU hardware fault signal.
module m20_rom_model (
    input wire [11:0] addr,
    output logic [15:0] data,
    output wire mapped
);
    logic [15:0] memory [0:4095];
    integer valid_words = 4096;
    integer read_delay_ps = 0;
    logic configuration_changed = 0;
    assign mapped = (addr < valid_words);
    task load(input string filename, input integer loaded_words, input integer delay_ps);
        integer i;
        begin
            for (i=0;i<4096;i=i+1) memory[i]=16'hFFFF;
            $readmemh(filename,memory);
            valid_words=loaded_words;
            read_delay_ps=delay_ps;
            configuration_changed=~configuration_changed;
        end
    endtask
    always @(addr or configuration_changed) begin
        #(read_delay_ps * 1ps);
        data=memory[addr];
    end
endmodule
