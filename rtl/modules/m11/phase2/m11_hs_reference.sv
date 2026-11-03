`default_nettype none
// Applied data is tagged at D launch. Base edge records the last stable D.
// Before the next D launch at T/4, launched and base-held describe the SAME
// transaction b[n-1] (at phi=0 the sampler sees the pre-edge launched value).
// Use the stable launch register for phi=0..3 to avoid a needlessly short
// base->early-sample path. This does not shift the expected transaction.
module m11_hs_reference #(parameter integer Q_PHASE=4,QM_PHASE=12)(
 input wire base_clk,rst,base_ce,
 input wire launched_data,input wire [30:0] launched_state,
 output wire q_expected,qm_expected,
 output wire [30:0] q_state,qm_state
);
 reg held;reg [30:0] held_state;
 always @(posedge base_clk) begin
   if(rst) begin held<=0;held_state<=0;end
   else if(base_ce) begin held<=launched_data;held_state<=launched_state;end
 end
 assign q_expected=(Q_PHASE<4)?launched_data:held;
 assign q_state=(Q_PHASE<4)?launched_state:held_state;
 assign qm_expected=(QM_PHASE<4 || QM_PHASE>=8)?launched_data:held;
 assign qm_state=(QM_PHASE<4 || QM_PHASE>=8)?launched_state:held_state;
endmodule
`default_nettype wire
