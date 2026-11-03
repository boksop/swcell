`timescale 1ns/1ps
// mode 0: asynchronous read; mode 1: registered-read FPGA adapter model.
// No reset port: resetting the CPU cannot clear this external memory.
module m20_ram_model (
    input wire clk,
    input wire [7:0] addr,
    input wire [3:0] wdata,
    input wire ce,
    input wire oe,
    input wire we,
    output wire [3:0] rdata
);
    logic [3:0] memory [0:255];
    logic [3:0] asynchronous_data = 4'hX;
    logic [3:0] synchronous_data = 4'hX;
    integer mode = 0;
    integer read_delay_ps = 0;
    integer write_count = 0;
    logic configuration_changed = 0;
    logic memory_changed = 0;
    assign rdata = mode == 1 ? synchronous_data : asynchronous_data;
    task load(input string filename, input integer memory_mode, input integer delay_ps);
        begin
            $readmemh(filename,memory);
            mode=memory_mode;
            read_delay_ps=delay_ps;
            write_count=0;
            synchronous_data=4'hX;
            configuration_changed=~configuration_changed;
        end
    endtask
    always @(addr or ce or oe or we or configuration_changed or memory_changed) begin
        #(read_delay_ps * 1ps);
        asynchronous_data=(ce && oe && !we) ? memory[addr] : 4'hX;
    end
    always @(posedge clk) begin
        if (ce && we) begin
            if (oe) $fatal(1,"RAM read/write conflict");
            if ($isunknown({addr,wdata})) $fatal(1,"RAM write contains X/Z");
            memory[addr] <= wdata;
            write_count <= write_count+1;
            memory_changed <= ~memory_changed;
        end
        if (ce && oe && !we && mode==1) begin
            #(read_delay_ps * 1ps);
            synchronous_data <= memory[addr];
        end
    end
endmodule
