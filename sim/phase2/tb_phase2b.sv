`timescale 1ns/1ps
// All 16 positions on each independent axis. The external latch model only
// sees physical D/CLK pins; independent pin-history assertions check reference
// transaction identity. No checker state drives the external Q/QM model.
module phase2b_case #(
 parameter integer HZ=75000000,Q=4,M=12,DELAY_CYCLE=0,
 parameter realtime MASTER_NS=0.4,SLAVE_NS=0.6
)(input wire sys,reset,output wire done,output wire [63:0] qe,me);
 localparam integer MULT=HZ==75000000?24:HZ==125000000?20:16;
 localparam integer DIV=HZ==75000000?16:8;
 wire bc,dc,qc,mc,bce,dce,qce,mce,lock,c,d,qd,md;
 wire [255:0] qp,mp;wire eqe,eme;
 swc_hs_clocks #(.FREQUENCY_HZ(HZ),.MULT(MULT),.DIVIDE(DIV),.Q_PHASE(Q),.QM_PHASE(M)) clocks(
 .sys_clk(sys),.rst(reset),.base_clk(bc),.d_clk(dc),.q_clk(qc),.qm_clk(mc),
 .base_ce(bce),.d_ce(dce),.q_ce(qce),.qm_ce(mce),.locked(lock),.clock_pin(c));
 reg master=0,slave=0,previous=0;
 always @(d or c) if(!c) master<=#(MASTER_NS) d;
 always @(master or c) if(c) slave<=#(SLAVE_NS) master;
 // Deliberate complete-cycle Q latency, independent of comparator reference.
 reg delayed_q=0;
 always @(posedge c) begin previous<=d;delayed_q<=#(SLAVE_NS) previous;end
 m11_hs_engine #(.Q_PHASE(Q),.QM_PHASE(M),.BITS(256)) engine(
 .base_clk(bc),.d_clk(dc),.q_clk(qc),.qm_clk(mc),.reset_n(!reset && lock),
 .base_ce(bce),.d_ce(dce),.q_ce(qce),.qm_ce(mce),
 .q_in(DELAY_CYCLE?delayed_q:slave),.qm_in(master),.data_pin(d),
 .q_payload(qp),.qm_payload(mp),.q_done(qd),.qm_done(md),.q_error_event(eqe),.qm_error_event(eme));
 assign done=qd&&md;
 assign qe=qp[191:128];assign me=mp[191:128];
 // For this independent scoreboard, latch the physical pin just BEFORE each
 // external rising edge (ODDR pin has a modeled delay). D cannot change here.
 reg captured_d=0;
 always @(posedge c) captured_d=d;
 always @(posedge qc) if(engine.run_q && !engine.qr && !qd) begin
   if(engine.eq!==((Q==0)?d:captured_d)) $fatal(1,"Q transaction alignment Q=%d M=%d",Q,M);
 end
 always @(posedge mc) if(engine.run_m && !engine.mr && !md) begin
   // At phase 0 the base pin rising edge has not happened yet, but D is stable
   // and already belongs to this incoming edge. Other high-half samples hold.
   if(engine.em!==((M==0 || M>=8)?d:captured_d))
     $fatal(1,"QM transaction alignment Q=%d M=%d",Q,M);
 end
 realtime lastbase=0;
 always @(posedge bc) lastbase=$realtime;
 always @(posedge qc) if(engine.run_q && !qd && lastbase>0) begin
   if(Q!=0 && (($realtime-lastbase)<(1.0e9/HZ*Q/16)-0.02 ||
               ($realtime-lastbase)>(1.0e9/HZ*Q/16)+0.02)) $fatal(1,"Actual Q sampling edge");
 end
 always @(posedge mc) if(engine.run_m && !md && lastbase>0) begin
   if(M!=0 && (($realtime-lastbase)<(1.0e9/HZ*M/16)-0.02 ||
               ($realtime-lastbase)>(1.0e9/HZ*M/16)+0.02)) $fatal(1,"Actual QM sampling edge");
 end
endmodule
module tb_phase2b #(parameter integer HZ=75000000);
 reg sys=0;always #10 sys=~sys;
 reg reset=1;initial #500 reset=0;
 wire [31:0] done;wire [63:0] qe[0:31],me[0:31];
 genvar p;
 generate for(p=0;p<16;p=p+1) begin:scan
   phase2b_case #(.HZ(HZ),.Q(p),.M(6)) q_axis(sys,reset,done[p],qe[p],me[p]);
   phase2b_case #(.HZ(HZ),.Q(12),.M(p)) m_axis(sys,reset,done[16+p],qe[16+p],me[16+p]);
 end endgenerate
 wire offset_done;wire [63:0] offset_qe,offset_me;
 phase2b_case #(.HZ(HZ),.Q(12),.M(6),.DELAY_CYCLE(1)) offset(sys,reset,offset_done,offset_qe,offset_me);
 integer i;
 initial begin
   wait((&done) && offset_done);#1;
   for(i=0;i<32;i=i+1) begin
     if(qe[i]>256 || me[i]>256) $fatal(1,"Counter range");
     $display("PHASE2B_SCAN HZ=%d axis=%s phase=%d qe=%d me=%d",HZ,i<16?"Q ":"QM",i%16,qe[i],me[i]);
   end
   if(qe[0]==0 || me[24]==0) $fatal(1,"Expected early sampling errors");
   if(qe[12]!=0 || me[22]!=0) $fatal(1,"Known stable sample must pass");
   if(offset_qe==0 || offset_me!=0) $fatal(1,"Complete-cycle latency must be detected only on Q");
   $display("PHASE2B_XSIM_PASS HZ=%d 32 independent points, alignment, early/stable, full-cycle fault",HZ);$finish;
 end
 initial begin #100000;$fatal(1,"Phase 2B scan timeout");end
endmodule
