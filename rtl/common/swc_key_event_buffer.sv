`default_nettype none
// Bank0 queues debounced press-state masks; bank1 retains press bits until read.
// No game rules: software still interprets both banks and decides all movement.
module swc_key_event_buffer #(
 parameter integer BANK0_BITS=4,BANK1_BITS=2,DEPTH=8,
 localparam integer PTR_BITS=$clog2(DEPTH),COUNT_BITS=$clog2(DEPTH+1)
)(input wire clk,rst,sample_ce,read0_ack,read1_ack,
 input wire[BANK0_BITS+BANK1_BITS-1:0] levels,press,consumed_keys,
 output wire[BANK0_BITS+BANK1_BITS-1:0] keys,
 output logic[COUNT_BITS-1:0] queued=0,output logic[9:0] overflows=0);
 logic[BANK0_BITS-1:0] fifo[0:DEPTH-1];
 logic[PTR_BITS-1:0] rd=0,wr=0;
 logic[BANK1_BITS-1:0] actions=0;
 logic presented=0;
 wire enqueue=|press[BANK0_BITS-1:0];
 wire pop=read0_ack&&presented&&queued!=0;
 wire push=enqueue&&(queued<DEPTH||pop);
 assign keys={levels[BANK0_BITS+:BANK1_BITS]|actions,
              queued!=0?fifo[rd]:levels[BANK0_BITS-1:0]};
 always_ff @(posedge clk)begin
  if(rst)begin rd<=0;wr<=0;queued<=0;overflows<=0;actions<=0;presented<=0;end
  else begin
   actions<=(actions&~(read1_ack?consumed_keys[BANK0_BITS+:BANK1_BITS]:{BANK1_BITS{1'b0}}))|press[BANK0_BITS+:BANK1_BITS];
   if(read0_ack)presented<=0;
   // If enqueue and CPU sampling coincide on an empty queue, the CPU already
   // saw that press via levels. Tag it presented to prevent duplicate delivery.
   if(sample_ce)presented<=queued!=0||push;
   if(push)begin fifo[wr]<=levels[BANK0_BITS-1:0];wr<=wr+1'b1;end
   if(pop)rd<=rd+1'b1;
   case({push,pop})2'b10:queued<=queued+1'b1;2'b01:queued<=queued-1'b1;default:begin end endcase
   if(enqueue&&!push&&overflows!=10'h3ff)overflows<=overflows+1'b1;
  end
 end
 // synthesis translate_off
 initial if(DEPTH<2||(1<<PTR_BITS)!=DEPTH||BANK0_BITS<1||BANK1_BITS<1)$fatal(1,"Invalid key buffer geometry");
 // synthesis translate_on
endmodule
`default_nettype wire
