`timescale 1ns/1ps
// Check every logical capture phase against the independently timed base clock.
// This deliberately instantiates simulation-only parallel static configurations.
module tb_hs_clock_grid #(parameter integer HZ=5000000);
 reg clk=0,rst=1;always #10 clk=~clk;
 initial begin repeat(16) @(negedge clk);rst=0;end
 function integer multiplier(input integer hz);
   case(hz) 5000000:multiplier=12;75000000,150000000,200000000:multiplier=24;
   125000000:multiplier=20;default:multiplier=16;endcase
 endfunction
 function integer divider(input integer hz);
   case(hz) 5000000:divider=120;10000000:divider=80;25000000:divider=32;
   50000000,75000000:divider=16;100000000,125000000,150000000:divider=8;
   200000000:divider=6;default:divider=32;endcase
 endfunction
 wire [15:0] finished;
 generate for(genvar p=0;p<16;p=p+1) begin:phase
   wire bc,dc,qc,mc,be,de,qe,me,lock,pin_clk;
   swc_hs_clocks #(.FREQUENCY_HZ(HZ),.MULT(multiplier(HZ)),.DIVIDE(divider(HZ)),
     .Q_PHASE(p),.QM_PHASE(p)) clocks(.sys_clk(clk),.rst(rst),
     .base_clk(bc),.d_clk(dc),.q_clk(qc),.qm_clk(mc),
     .base_ce(be),.d_ce(de),.q_ce(qe),.qm_ce(me),.locked(lock),.clock_pin(pin_clk));
   realtime base_time=-1,period_ns=1.0e9/HZ,qdelta,mdelta;
   localparam realtime TARGET=(HZ==1000000)?((p*50+8)/16)*20.0:p*1.0e9/HZ/16.0;
   integer bases=0,qs=0,ms=0;
   always @(posedge bc) if(!rst && lock && be) begin
     base_time=$realtime;bases=bases+1;
   end
   always @(posedge qc) if(!rst && lock && qe && bases>16) begin
     qdelta=$realtime-base_time;
     if(qdelta>period_ns-0.02) qdelta=qdelta-period_ns;
     if(qdelta<TARGET-0.02 || qdelta>TARGET+0.02)
       $fatal(1,"Q phase grid hz=%d p=%d actual=%f target=%f",HZ,p,qdelta,TARGET);
     qs=qs+1;
   end
   always @(posedge mc) if(!rst && lock && me && bases>16) begin
     mdelta=$realtime-base_time;
     if(mdelta>period_ns-0.02) mdelta=mdelta-period_ns;
     if(mdelta<TARGET-0.02 || mdelta>TARGET+0.02)
       $fatal(1,"QM phase grid hz=%d p=%d actual=%f target=%f",HZ,p,mdelta,TARGET);
     ms=ms+1;
   end
   assign finished[p]=qs>=16 && ms>=16;
 end endgenerate
 initial begin
   wait(&finished);$display("HS_CLOCK_GRID_PASS hz=%d q_phases=16 qm_phases=16",HZ);$finish;
 end
 initial begin #1000000;$fatal(1,"Clock grid timeout");end
endmodule
