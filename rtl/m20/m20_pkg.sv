`default_nettype none
// Frozen ISA: M20-300-ISA-0.1. These internal op/state encodings are NOT ISA words.
package m20_pkg;
    localparam logic [5:0] OP_LOAD     = 6'd0;
    localparam logic [5:0] OP_ADD      = 6'd1;
    localparam logic [5:0] OP_ADC      = 6'd2;
    localparam logic [5:0] OP_SUB      = 6'd3;
    localparam logic [5:0] OP_SBC      = 6'd4;
    localparam logic [5:0] OP_CMP      = 6'd5;
    localparam logic [5:0] OP_AND      = 6'd6;
    localparam logic [5:0] OP_XOR      = 6'd7;
    localparam logic [5:0] OP_OR       = 6'd8;
    localparam logic [5:0] OP_NOT      = 6'd9;
    localparam logic [5:0] OP_SHL      = 6'd10;
    localparam logic [5:0] OP_SHR      = 6'd11;
    localparam logic [5:0] OP_ST       = 6'd12;
    localparam logic [5:0] OP_ARL      = 6'd13;
    localparam logic [5:0] OP_ARH      = 6'd14;
    localparam logic [5:0] OP_MOVARL   = 6'd15;
    localparam logic [5:0] OP_MOVARH   = 6'd16;
    localparam logic [5:0] OP_MOVA_ARL = 6'd17;
    localparam logic [5:0] OP_MOVA_ARH = 6'd18;
    localparam logic [5:0] OP_INCAR    = 6'd19;
    localparam logic [5:0] OP_JMP      = 6'd20;
    localparam logic [5:0] OP_JZ       = 6'd21;
    localparam logic [5:0] OP_JC       = 6'd22;
    localparam logic [5:0] OP_IN0      = 6'd23;
    localparam logic [5:0] OP_IN1      = 6'd24;
    localparam logic [5:0] OP_OUT      = 6'd25;
    localparam logic [5:0] OP_NOP      = 6'd26;
    localparam logic [5:0] OP_HALT     = 6'd27;
    localparam logic [5:0] OP_INVALID  = 6'd63;

    localparam logic [2:0] S_RESET       = 3'd0;
    localparam logic [2:0] S_FETCH_WAIT  = 3'd1;
    localparam logic [2:0] S_EXEC        = 3'd2;
    localparam logic [2:0] S_MEM_SETUP   = 3'd3;
    localparam logic [2:0] S_MEM_ACCESS  = 3'd4;
    localparam logic [2:0] S_MEM_RELEASE = 3'd5;
    localparam logic [2:0] S_HALT        = 3'd6;
    localparam logic [2:0] S_TRAP        = 3'd7;
endpackage
`default_nettype wire
