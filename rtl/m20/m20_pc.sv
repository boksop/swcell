`default_nettype none
module m20_pc (
    input wire clk,
    input wire rst,
    input wire write_enable,
    input wire [11:0] write_value,
    output logic [11:0] value
);
    always_ff @(posedge clk) begin
        if (rst) value <= 12'h000;
        else if (write_enable) value <= write_value;
    end
endmodule
`default_nettype wire
