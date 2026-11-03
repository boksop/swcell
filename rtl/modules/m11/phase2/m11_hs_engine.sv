`default_nettype none
module m11_hs_engine #(
 parameter integer Q_PHASE=4,QM_PHASE=12,PATTERN=5,
 parameter [63:0] BITS=64'd1000000
)(input wire base_clk,d_clk,q_clk,qm_clk,reset_n,
 input wire base_ce,d_ce,q_ce,qm_ce,
 input wire q_in,qm_in,
 output wire data_pin,output wire [255:0] q_payload,qm_payload,
 output wire q_done,qm_done,
 output wire q_error_event,qm_error_event
);
 wire br,dr,qr,mr;
 swc_reset_sync rb(.clk(base_clk),.reset_n(reset_n),.rst(br));
 swc_reset_sync rd(.clk(d_clk),.reset_n(reset_n),.rst(dr));
 swc_reset_sync rq(.clk(q_clk),.reset_n(reset_n),.rst(qr));
 swc_reset_sync rm(.clk(qm_clk),.reset_n(reset_n),.rst(mr));
 reg [7:0] warmup;
 always @(posedge base_clk) begin
   if(br) warmup<=0;
   else if(base_ce && warmup!=255) warmup<=warmup+1'b1;
 end
 // Initialization: D=0 for 32 D-domain cycles. Thereafter deterministic
 // PRBS warmup is excluded from checks. UART never controls this sequence.
 wire [30:0] prbs;
 wire launched_data;
 wire [30:0] launched_state;
 wire finish_d,finish_q,finish_m;
 swc_input_sync #(.WIDTH(1)) finish_q_sync(.clk(d_clk),.rst(dr),
   .async_in(q_done),.sync_out(finish_q));
 swc_input_sync #(.WIDTH(1)) finish_m_sync(.clk(d_clk),.rst(dr),
   .async_in(qm_done),.sync_out(finish_m));
 assign finish_d=finish_q && finish_m;
 wire advancing,bit_value;
 swc_hs_pattern_driver #(.PATTERN(PATTERN)) driver(.clk(d_clk),.rst(dr),.ce(d_ce),.stopped(finish_d),
   .pin_data(data_pin),.advancing(advancing),.bit_value(bit_value),
   .launched_data(launched_data),.launched_state(launched_state),.sequence_state(prbs));
 wire eq,em;wire [30:0] sq,sm;
 m11_hs_reference #(.Q_PHASE(Q_PHASE),.QM_PHASE(QM_PHASE)) reference(
   .base_clk(base_clk),.rst(br),.base_ce(base_ce),.launched_data(launched_data),
   .launched_state(launched_state),.q_expected(eq),.qm_expected(em),.q_state(sq),.qm_state(sm));
 wire run=warmup>=128;
 // Start is a slow, persistent control; synchronize it locally. Payload and
 // expected data retain their explicitly timed, related-clock paths.
 wire run_q,run_m;
 swc_input_sync #(.WIDTH(1)) run_q_sync(.clk(q_clk),.rst(qr),
   .async_in(run),.sync_out(run_q));
 swc_input_sync #(.WIDTH(1)) run_m_sync(.clk(qm_clk),.rst(mr),
   .async_in(run),.sync_out(run_m));
 wire [63:0] qt,qe,qf,mt,me,mf;
 wire qa,qx,ma,mx;wire [30:0] qs,qstart,ms,mstart;
 swc_capture_lane #(.LIMIT(BITS)) q_lane(.clk(q_clk),.rst(qr),.enable(run_q),.sample_ce(q_ce),
   .actual(q_in),.expected(eq),.expected_state(sq),.done(q_done),.total_bits(qt),.errors(qe),
   .first_cycle(qf),.first_expected(qx),.first_actual(qa),.first_state(qs),.start_state(qstart),.error_event(q_error_event));
 swc_capture_lane #(.LIMIT(BITS)) qm_lane(.clk(qm_clk),.rst(mr),.enable(run_m),.sample_ce(qm_ce),
   .actual(qm_in),.expected(em),.expected_state(sm),.done(qm_done),.total_bits(mt),.errors(me),
   .first_cycle(mf),.first_expected(mx),.first_actual(ma),.first_state(ms),.start_state(mstart),.error_event(qm_error_event));
 // 256-bit immutable packets; both lane counters remain local to their clocks.
 assign q_payload={qt,qe,qf,qx,qa,qs,qstart};
 assign qm_payload={mt,me,mf,mx,ma,ms,mstart};
endmodule
`default_nettype wire
