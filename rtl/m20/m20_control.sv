`default_nettype none
// No instruction/data latches. uSTATE is the only control state (three bits).
module m20_control (
    input wire clk,
    input wire rst,
    input wire legal,
    input wire is_memory,
    input wire halt_instruction,
    output wire [2:0] state
);
    import m20_pkg::*;
    logic [2:0] state_reg;
    logic [2:0] state_next;
    assign state = state_reg;
    always_comb begin
        state_next = state_reg;
        case (state_reg)
            S_RESET:       state_next = S_FETCH_WAIT;
            S_FETCH_WAIT:  state_next = S_EXEC;
            S_EXEC: begin
                if (!legal) state_next = S_TRAP;
                else if (is_memory) state_next = S_MEM_SETUP;
                else if (halt_instruction) state_next = S_HALT;
                else state_next = S_FETCH_WAIT;
            end
            S_MEM_SETUP:   state_next = S_MEM_ACCESS;
            S_MEM_ACCESS:  state_next = S_MEM_RELEASE;
            S_MEM_RELEASE: state_next = S_FETCH_WAIT;
            S_HALT:        state_next = S_HALT;
            S_TRAP:        state_next = S_TRAP;
            default:       state_next = S_RESET;
        endcase
    end
    always_ff @(posedge clk) begin
        if (rst) state_reg <= S_RESET;
        else state_reg <= state_next;
    end
endmodule
`default_nettype wire
