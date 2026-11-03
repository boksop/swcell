`default_nettype none
module m20_ar (
    input wire clk,
    input wire rst,
    input wire write_enable,
    input wire [7:0] write_value,
    output logic [7:0] value
);
    always_ff @(posedge clk) begin
        if (rst) value <= 8'h00;
        else if (write_enable) value <= write_value;
    end
endmodule
`default_nettype wire
