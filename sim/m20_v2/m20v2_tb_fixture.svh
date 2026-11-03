// Included inside simulation tops only; no state here belongs to the CPU.
logic clk=0;
always #5 clk=~clk;
logic rst=1;
logic [5:0] keys=0;
wire [11:0] rom_addr;
wire [15:0] rom_data;
wire rom_mapped;
wire [7:0] ram_addr;
wire [3:0] ram_wdata,ram_rdata;
wire ram_ce,ram_oe,ram_we;
wire [11:0] dbg_pc;
wire [3:0] dbg_a;
wire [7:0] dbg_ar;
wire dbg_z,dbg_c;
wire [3:0] dbg_gpo;
wire [2:0] dbg_state;
wire halted,trapped;
wire retire_valid;
wire [11:0] retire_pc,retire_next_pc;
wire [15:0] retire_instruction;
wire [3:0] retire_a;
wire [7:0] retire_ar;
wire retire_z,retire_c;
wire [3:0] retire_gpo;
wire retire_ram_valid,retire_ram_write;
wire [7:0] retire_ram_addr;
wire [3:0] retire_ram_wdata,retire_ram_rdata;
wire retire_is_memory;
wire [2:0] retire_instruction_cycles;
m20v2_cpu_core dut(.*);
m20_rom_model rom(.addr(rom_addr),.data(rom_data),.mapped(rom_mapped));
m20_ram_model ram(.clk(clk),.addr(ram_addr),.wdata(ram_wdata),.rdata(ram_rdata),
    .ce(ram_ce),.oe(ram_oe),.we(ram_we));

// Independent immutable V1 reference core and separate memory models.
wire [11:0] ref_rom_addr;
wire [15:0] ref_rom_data;
wire [7:0] ref_ram_addr;
wire [3:0] ref_ram_wdata;
wire [3:0] ref_ram_rdata;
wire ref_ram_ce;
wire ref_ram_oe;
wire ref_ram_we;
wire [11:0] ref_dbg_pc;
wire [3:0] ref_dbg_a;
wire [7:0] ref_dbg_ar;
wire ref_dbg_z;
wire ref_dbg_c;
wire [3:0] ref_dbg_gpo;
wire [2:0] ref_dbg_state;
wire ref_halted;
wire ref_trapped;
wire ref_retire_valid;
wire [11:0] ref_retire_pc;
wire [11:0] ref_retire_next_pc;
wire [15:0] ref_retire_instruction;
wire [3:0] ref_retire_a;
wire [7:0] ref_retire_ar;
wire ref_retire_z;
wire ref_retire_c;
wire [3:0] ref_retire_gpo;
wire ref_retire_ram_valid;
wire ref_retire_ram_write;
wire [7:0] ref_retire_ram_addr;
wire [3:0] ref_retire_ram_wdata;
wire [3:0] ref_retire_ram_rdata;
wire ref_retire_is_memory;
wire [2:0] ref_retire_instruction_cycles;
wire ref_rom_mapped;
m20_cpu_core ref_dut(
    .clk(clk),.rst(rst),.keys(keys),
    .rom_addr(ref_rom_addr),
    .rom_data(ref_rom_data),
    .ram_addr(ref_ram_addr),
    .ram_wdata(ref_ram_wdata),
    .ram_rdata(ref_ram_rdata),
    .ram_ce(ref_ram_ce),
    .ram_oe(ref_ram_oe),
    .ram_we(ref_ram_we),
    .dbg_pc(ref_dbg_pc),
    .dbg_a(ref_dbg_a),
    .dbg_ar(ref_dbg_ar),
    .dbg_z(ref_dbg_z),
    .dbg_c(ref_dbg_c),
    .dbg_gpo(ref_dbg_gpo),
    .dbg_state(ref_dbg_state),
    .halted(ref_halted),
    .trapped(ref_trapped),
    .retire_valid(ref_retire_valid),
    .retire_pc(ref_retire_pc),
    .retire_next_pc(ref_retire_next_pc),
    .retire_instruction(ref_retire_instruction),
    .retire_a(ref_retire_a),
    .retire_ar(ref_retire_ar),
    .retire_z(ref_retire_z),
    .retire_c(ref_retire_c),
    .retire_gpo(ref_retire_gpo),
    .retire_ram_valid(ref_retire_ram_valid),
    .retire_ram_write(ref_retire_ram_write),
    .retire_ram_addr(ref_retire_ram_addr),
    .retire_ram_wdata(ref_retire_ram_wdata),
    .retire_ram_rdata(ref_retire_ram_rdata),
    .retire_is_memory(ref_retire_is_memory),
    .retire_instruction_cycles(ref_retire_instruction_cycles)
);
m20_rom_model ref_rom(.addr(ref_rom_addr),.data(ref_rom_data),.mapped(ref_rom_mapped));
m20_ram_model ref_ram(.clk(clk),.addr(ref_ram_addr),.wdata(ref_ram_wdata),.rdata(ref_ram_rdata),.ce(ref_ram_ce),.oe(ref_ram_oe),.we(ref_ram_we));

logic lockstep_enabled=0;
longint unsigned lockstep_cycles=0;
task check_v1_v2_state;
    begin
        if ({dbg_pc,dbg_ar,dbg_a,dbg_z,dbg_c,dbg_gpo,dbg_state,halted,trapped} !==
            {ref_dbg_pc,ref_dbg_ar,ref_dbg_a,ref_dbg_z,ref_dbg_c,ref_dbg_gpo,ref_dbg_state,ref_halted,ref_trapped})
            $fatal(1,"V1/V2 architectural/control state mismatch at time=%0t pc=%h ref_pc=%h",$time,dbg_pc,ref_dbg_pc);
        if ({rom_addr,ram_ce,ram_oe,ram_we,retire_valid} !==
            {ref_rom_addr,ref_ram_ce,ref_ram_oe,ref_ram_we,ref_retire_valid})
            $fatal(1,"V1/V2 transaction control mismatch at time=%0t",$time);
        if (ram_ce && ram_addr!==ref_ram_addr) $fatal(1,"V1/V2 active RAM address mismatch");
        if (ram_we && ram_wdata!==ref_ram_wdata) $fatal(1,"V1/V2 write data mismatch");
    end
endtask
always @(posedge clk) begin
    if(lockstep_enabled && !rst) begin
        check_v1_v2_state();
        if(retire_valid) begin
            if({retire_pc,retire_instruction,retire_next_pc,retire_a,retire_ar,retire_z,retire_c,retire_gpo,
                retire_ram_valid,retire_ram_write,retire_is_memory,retire_instruction_cycles} !==
               {ref_retire_pc,ref_retire_instruction,ref_retire_next_pc,ref_retire_a,ref_retire_ar,ref_retire_z,ref_retire_c,ref_retire_gpo,
                ref_retire_ram_valid,ref_retire_ram_write,ref_retire_is_memory,ref_retire_instruction_cycles})
                $fatal(1,"V1/V2 retirement projection mismatch at PC=%h",retire_pc);
            if(retire_ram_valid && retire_ram_addr!==ref_retire_ram_addr) $fatal(1,"V1/V2 retire RAM address");
            if(retire_ram_valid && retire_ram_write && retire_ram_wdata!==ref_retire_ram_wdata)
                $fatal(1,"V1/V2 retire RAM write data");
            if(retire_ram_valid && !retire_ram_write && retire_ram_rdata!==ref_retire_ram_rdata)
                $fatal(1,"V1/V2 retire RAM read data");
        end
        lockstep_cycles=lockstep_cycles+1;
    end
    #1ps;
    if(lockstep_enabled) check_v1_v2_state();
end
