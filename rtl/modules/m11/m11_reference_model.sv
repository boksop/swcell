`default_nettype none
// Golden state advances only when a new stimulus transaction is applied.
// No comparison occurs until the common timer has allowed IO+CDC settling.
module m11_reference_model(input wire clk, rst, apply,
 input wire dl_d, dl_en, dff_d, dff_clk,
 output wire [2:0] expected);
 reg dl_q, qm, q;
 wire next_master=dff_clk?qm:dff_d;
 always @(posedge clk) begin
   if(rst) begin dl_q<=0; qm<=0; q<=0; end
   else if(apply) begin
     if(dl_en) dl_q<=dl_d;
     qm<=next_master;
     // Use the new master when transparent low, and stored master when high.
     // In particular the rising edge consumes the LAST low-phase sample.
     if(dff_clk) q<=next_master;
   end
 end
 assign expected={qm,q,dl_q};
endmodule
`default_nettype wire
