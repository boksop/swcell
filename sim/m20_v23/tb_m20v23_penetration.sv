`timescale 1ns/1ps
// Negative witness: changing D AFTER the intended capture traverses both open MUXes.
module tb_m20v23_penetration;
 logic master_hold=0,slave_open=0,d=0,checks_enable=0;
 wire q,qm;
 integer tf;
 initial begin tf=$fopen("penetration.csv","w");$fwrite(tf,"time_ns,master_hold,slave_open,effective_master_hold,effective_slave_open,d,qm,q\n");end
 always @(master_hold or slave_open or cell_dut.master.s_eff or cell_dut.slave.s_eff or d or qm or q)begin #1ps;$fwrite(tf,"%0.3f,%b,%b,%b,%b,%b,%b,%b\n",$realtime,master_hold,slave_open,cell_dut.master.s_eff,cell_dut.slave.s_eff,d,qm,q);end
 `ifdef V23_EXPECT_FATAL
 localparam bit CF=1;
 `else
 localparam bit CF=0;
 `endif
 swc_ms_bit_v23 #(.DATA_NS(1),.SELECT_NS(0.5),.MASTER_NS(12),.SLAVE_NS(0),.CHECK_FATAL(CF)) cell_dut(.*);
 initial begin
  #30;master_hold=1;#30;slave_open=1;#30;slave_open=0;#30;
  if(q!==0 || qm!==0)$fatal(1,"penetration init");
  master_hold=0;#30;checks_enable=1;
  // Both raw controls switch together, but the Master branch closes 12ns later.
  master_hold=1;slave_open=1;#3;d=1;#5;
  if(q!==1 || qm!==1 || cell_dut.overlap_events==0)$fatal(1,"negative failed to expose real data penetration");
  $display("M20V23_PENETRATION_PASS expected_old_q=0 actual_q=%b overlap_events=%0d",q,cell_dut.overlap_events);
  #20;$finish;
 end
 initial begin #1000;$fatal(1,"penetration watchdog");end
endmodule
