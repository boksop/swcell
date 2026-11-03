`default_nettype none
module swc_sequence_gen(input wire clk, rst, restart, advance,
 input wire [2:0] mode, output reg data, output wire auxiliary);
 // 0=zero, 1=one, 2=0101, 3=0011, 4=00001111, 5=PRBS31
 reg [2:0] index;
 wire random_bit;
 wire [30:0] random_state;
 swc_prbs31 prbs(.clk(clk),.rst(rst),.restart(restart),.advance(advance),
   .bit_out(random_bit),.state_out(random_state));
 always @(posedge clk)
   if (rst || restart) index<=0;
   else if (advance) index<=index+1'b1;
 always @* case(mode)
   0:data=0; 1:data=1; 2:data=index[0]; 3:data=index[1];
   4:data=index[2]; default:data=random_bit;
 endcase
 assign auxiliary=random_state[15];
endmodule
`default_nettype wire
