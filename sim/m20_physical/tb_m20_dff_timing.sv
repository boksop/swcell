`timescale 1ns/1ps
module tb_m20_dff_timing;
 reg mh=0,so=0;reg [3:0] d=0;wire [3:0] q,qm;
 reg cm=0,cs=0,cd=0;wire cq,cqm;
 swc_two_mux_dff_timed #(.WIDTH(4)) safe(.master_hold(mh),.slave_open(so),.d(d),.q(q),.qm(qm));
 swc_two_mux_dff_timed #(.MASTER_SELECT_NS(8),.SLAVE_SELECT_NS(1)) race(.master_hold(cm),.slave_open(cs),.d(cd),.q(cq),.qm(cqm));
 integer i,checks=0;
 task safe_capture;
  begin mh=1;#10;so=1;#10;end
 endtask
 task safe_low;
  begin so=0;#10;mh=0;#10;end
 endtask
 initial begin
  #30;safe_capture();if(q!==0)$fatal(1,"transparent initialization failed");
  for(i=0;i<16;i=i+1)begin
   d=i[3:0];#10;if(q!==(i==0?4'd0:(i-1)))$fatal(1,"master hold failed");
   safe_low();if(qm!==d)$fatal(1,"master transparency failed");
   safe_capture();if(q!==d)$fatal(1,"nonoverlap capture failed");checks=checks+1;
  end
  $display("NONOVERLAP_MODEL_PASS captures=%0d WIDTH=4 DATA_NS=2 SELECT_NS=2 gap_ns=10",checks);
 end
 initial begin
  #30;cm=1;#12;cs=1;#12;
  if(cq!==0)$fatal(1,"race fixture init failed");
  cs=0;#10;cm=0;#20;cd=0;#10;
  // Same nominal rising edge, master closes 8ns later; slave opens after1ns.
  cm=1;cs=1;#2;cd=1;#5;
  if(cq!==1)$fatal(1,"expected race was not observed");
  $display("EXPECTED_RACE_OBSERVED new_D_passed_with_master_close_late=1");
 end
 initial begin #1000;$display("M20_DFF_TIMING_MODEL_PASS illustrative_only=1");$finish;end
endmodule
