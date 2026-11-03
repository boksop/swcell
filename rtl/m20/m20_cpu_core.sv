`default_nettype none
// M20-300-ISA-0.1 functional reference RTL, V1 timing profile 0.1.
// Exactly 33 functional FF bits; all retire/debug signals below are combinational.
module m20_cpu_core (
    input  wire clk,
    input  wire rst,
    input  wire [5:0] keys,
    output wire [11:0] rom_addr,
    input  wire [15:0] rom_data,
    output wire [7:0] ram_addr,
    output wire [3:0] ram_wdata,
    input  wire [3:0] ram_rdata,
    output wire ram_ce,
    output wire ram_oe,
    output wire ram_we,
    output wire [11:0] dbg_pc,
    output wire [3:0] dbg_a,
    output wire [7:0] dbg_ar,
    output wire dbg_z,
    output wire dbg_c,
    output wire [3:0] dbg_gpo,
    output wire [2:0] dbg_state,
    output wire halted,
    output wire trapped,
    output wire retire_valid,
    output wire [11:0] retire_pc,
    output wire [15:0] retire_instruction,
    output wire [11:0] retire_next_pc,
    output wire [3:0] retire_a,
    output wire [7:0] retire_ar,
    output wire retire_z,
    output wire retire_c,
    output wire [3:0] retire_gpo,
    output wire retire_ram_valid,
    output wire retire_ram_write,
    output wire [7:0] retire_ram_addr,
    output wire [3:0] retire_ram_wdata,
    output wire [3:0] retire_ram_rdata,
    output wire retire_is_memory,
    output wire [2:0] retire_instruction_cycles
);
    import m20_pkg::*;
    wire [11:0] pc_value;
    wire [7:0] ar_value;
    logic [3:0] a_reg;
    logic z_reg;
    logic c_reg;
    logic [3:0] gpo_reg;
    wire [2:0] state;
    wire legal, is_memory, memory_write, indirect;
    wire [5:0] op;
    wire [3:0] alu_result;
    wire alu_z, alu_c, alu_a_we, alu_z_we, alu_c_we;
    logic [3:0] alu_operand;
    logic [11:0] next_pc;
    logic [7:0] next_ar;
    logic ar_we;
    wire [3:0] next_a;
    wire next_z, next_c;
    wire [3:0] next_gpo;
    wire in_memory;

    m20_decoder u_decoder (
        .instruction(rom_data), .legal(legal), .is_memory(is_memory),
        .memory_write(memory_write), .indirect(indirect), .op(op)
    );
    m20_control u_control (
        .clk(clk), .rst(rst), .legal(legal), .is_memory(is_memory),
        .halt_instruction(op == OP_HALT), .state(state)
    );
    m20_pc u_pc (
        .clk(clk), .rst(rst), .write_enable(retire_valid),
        .write_value(next_pc), .value(pc_value)
    );
    m20_ar u_ar (
        .clk(clk), .rst(rst), .write_enable(retire_valid && ar_we),
        .write_value(next_ar), .value(ar_value)
    );
    m20_alu u_alu (
        .op(op), .a(a_reg), .operand(alu_operand), .c_in(c_reg),
        .result(alu_result), .z_out(alu_z), .c_out(alu_c),
        .a_we(alu_a_we), .z_we(alu_z_we), .c_we(alu_c_we)
    );

    // Operand selection has no latches: ROM/address remain stable until retire.
    always_comb begin
        alu_operand = is_memory ? ram_rdata : rom_data[3:0];
        case (op)
            OP_MOVA_ARL: alu_operand = ar_value[3:0];
            OP_MOVA_ARH: alu_operand = ar_value[7:4];
            OP_IN0: alu_operand = keys[3:0];
            OP_IN1: alu_operand = {2'b00, keys[5:4]};
            default: begin end
        endcase
    end

    always_comb begin
        next_pc = pc_value + 12'd1;
        if ((op == OP_JMP) || ((op == OP_JZ) && z_reg) ||
            ((op == OP_JC) && c_reg)) next_pc = rom_data[11:0];
        next_ar = ar_value;
        ar_we = 1'b1;
        case (op)
            OP_ARL: next_ar = {ar_value[7:4], rom_data[3:0]};
            OP_ARH: next_ar = {rom_data[3:0], ar_value[3:0]};
            OP_MOVARL: next_ar = {ar_value[7:4], a_reg};
            OP_MOVARH: next_ar = {a_reg, ar_value[3:0]};
            OP_INCAR: next_ar = ar_value + 8'd1;
            default: ar_we = 1'b0;
        endcase
    end

    assign next_a = alu_a_we ? alu_result : a_reg;
    assign next_z = alu_z_we ? alu_z : z_reg;
    assign next_c = alu_c_we ? alu_c : c_reg;
    assign next_gpo = (op == OP_OUT) ? a_reg : gpo_reg;
    always_ff @(posedge clk) begin
        if (rst) begin
            a_reg <= 4'h0;
            z_reg <= 1'b1;
            c_reg <= 1'b0;
            gpo_reg <= 4'h8;
        end else if (retire_valid) begin
            if (alu_a_we) a_reg <= alu_result;
            if (alu_z_we) z_reg <= alu_z;
            if (alu_c_we) c_reg <= alu_c;
            if (op == OP_OUT) gpo_reg <= a_reg;
        end
    end

    assign rom_addr = pc_value;
    assign ram_addr = indirect ? ar_value : rom_data[7:0];
    assign ram_wdata = a_reg;
    assign in_memory = (state == S_MEM_SETUP) || (state == S_MEM_ACCESS) ||
                       (state == S_MEM_RELEASE);
    // rst immediately suppresses a pending write even before the reset edge.
    assign ram_ce = !rst && legal && is_memory && in_memory;
    assign ram_oe = ram_ce && !memory_write;
    assign ram_we = ram_ce && memory_write && (state == S_MEM_ACCESS);

    assign retire_valid = !rst && legal &&
                          (((state == S_EXEC) && !is_memory) ||
                           ((state == S_MEM_RELEASE) && is_memory));
    assign retire_pc = pc_value;
    assign retire_instruction = rom_data;
    assign retire_next_pc = next_pc;
    assign retire_a = next_a;
    assign retire_ar = next_ar;
    assign retire_z = next_z;
    assign retire_c = next_c;
    assign retire_gpo = next_gpo;
    assign retire_is_memory = is_memory;
    assign retire_ram_valid = retire_valid && is_memory;
    assign retire_ram_write = retire_ram_valid && memory_write;
    assign retire_ram_addr = ram_addr;
    assign retire_ram_wdata = a_reg;
    assign retire_ram_rdata = ram_rdata;
    assign retire_instruction_cycles = is_memory ? 3'd5 : 3'd2;

    assign dbg_pc = pc_value;
    assign dbg_a = a_reg;
    assign dbg_ar = ar_value;
    assign dbg_z = z_reg;
    assign dbg_c = c_reg;
    assign dbg_gpo = gpo_reg;
    assign dbg_state = state;
    assign halted = (state == S_HALT);
    assign trapped = (state == S_TRAP);
endmodule
`default_nettype wire
