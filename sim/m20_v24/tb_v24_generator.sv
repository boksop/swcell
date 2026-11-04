`timescale 1ns/1ps
module tb_v24_generator;
 logic clk_ref=0,osc_on=1,rst=1,run_request=0,step_request=0;
 always begin #500;if(osc_on)clk_ref=~clk_ref;end
 wire master_hold,slave_open,busy,step_ack,fault,local_h,local_s;
 wire [3:0] phase_state;
 `ifdef V24_FAST
 localparam real CDEL=0.2,IL=0.8,LD=0.1,LS=0.2,BS=0.02,BASE=0.05;
 `elsif V24_SLOW
 localparam real CDEL=2,IL=6,LD=1,LS=2,BS=0.2,BASE=1;
 `else
 localparam real CDEL=0.5,IL=2,LD=0.2,LS=0.3,BS=0.05,BASE=0.1;
 `endif
 `ifdef V24_BAD_SKEW
 localparam real MS=20;
 `else
 localparam real MS=BASE;
 `endif
 swc157_phasegen_v24 #(.COMB_NS(CDEL),.INTERLOCK_NS(IL),.LOCAL_DATA_NS(LD),.LOCAL_SELECT_NS(LS),.LOCAL_MASTER_NS(MS),.LOCAL_SLAVE_NS(BASE),.LOCAL_SKEW_NS(BS)) dut(.*);
 logic [3:0] injected;integer bad_count=0;
 function automatic bit legal(input integer q);
  legal=(q==0 || q==1 || q==3 || q==7 || q==15 || q==14 || q==12 || q==8);
 endfunction
 task inject_illegal(input integer value);
  begin
   run_request=0;step_request=0;reset_gen();
   @(negedge clk_ref);#100;injected=value;
   force dut.r0.d=injected[0];force dut.r1.d=injected[1];force dut.r2.d=injected[2];force dut.r3.d=injected[3];
   @(posedge clk_ref);#100;
   release dut.r0.d;release dut.r1.d;release dut.r2.d;release dut.r3.d;
   if(phase_state!==injected)$fatal(1,"illegal injection not captured");
   repeat(3)@(negedge clk_ref);#100;
   if(fault!==1 || phase_state!==8 || busy || master_hold!==1 || slave_open!==0)$fatal(1,"V24_ILLEGAL_RECOVERY");
   run_request=1;repeat(3)@(negedge clk_ref);#100;if(busy || !fault)$fatal(1,"fault resumed without reset");
   bad_count=bad_count+1;
  end
 endtask
 integer commits=0,steps=0,i,loops,transitions=0;logic checking=0;
 logic [3:0] old_phase;
 realtime m_opened=-1e9,s_opened=-1e9;
 always @(negedge master_hold)if(checking && !rst)m_opened=$realtime;
 always @(posedge master_hold)if(checking && !rst && $realtime-m_opened<2900)$fatal(1,"V24_MASTER_RUNT");
 always @(posedge slave_open)if(checking && !rst)s_opened=$realtime;
 always @(negedge slave_open)if(checking && !rst && $realtime-s_opened<2900)$fatal(1,"V24_SLAVE_RUNT");
 always @(posedge master_hold)if(checking && !rst)commits=commits+1;
 always @(master_hold or slave_open)begin #1;if(!master_hold && slave_open)$fatal(1,"V24_OUTPUT_OVERLAP");end
 always @(negedge clk_ref)begin #100;if(checking && !rst && busy && !$isunknown(phase_state))begin
  if(phase_state!==old_phase)begin
   if(phase_state!=={old_phase[2:0],~old_phase[3]})$fatal(1,"V24_BAD_SEQUENCE %b ->%b",old_phase,phase_state);
   old_phase=phase_state;transitions=transitions+1;
  end
 end end
 task reset_gen;
  begin rst=1;repeat(4)@(negedge clk_ref);#100;
   if(phase_state!==8 || busy!==0 || fault!==0 || master_hold!==1 || slave_open!==0)$fatal(1,"V24_RESET");
   rst=0;old_phase=8;
  end
 endtask
 task step_once;
  integer commits_at_start;
  begin commits_at_start=commits;step_request=~step_request;wait(busy);wait(step_ack==step_request);#100;
   if(busy || phase_state!==8 || commits!=commits_at_start+1 || master_hold!==1 || slave_open!==0)$fatal(1,"V24_STEP");
   steps=steps+1;repeat(4)@(negedge clk_ref);#100;if(busy || commits!=commits_at_start+1)$fatal(1,"V24_STEP_REPEATED");
  end
 endtask
 initial begin
  reset_gen();checking=1;repeat(5)step_once();
  run_request=1;wait(busy);repeat(25)@(negedge clk_ref);run_request=0;wait(!busy);#100;
  if(phase_state!==8 || master_hold!==1 || slave_open!==0)$fatal(1,"V24_STOP");
  step_once();checking=0;
  // Loss can freeze Slave open. External reset clamps outputs even without root edges.
  run_request=1;wait(slave_open);#100;osc_on=0;#5000;
  rst=1;#100;if(master_hold!==1 || slave_open!==0)$fatal(1,"V24_LOSS_CLAMP");
  osc_on=1;run_request=0;step_request=0;reset_gen();
  for(i=0;i<16;i=i+1)if(!legal(i))inject_illegal(i);
  run_request=0;reset_gen();
  $display("V24_GENERATOR_PASS steps=%0d transitions=%0d reset_stop_loss=1 illegal_recovered=%0d",steps,transitions,bad_count);$finish;
 end
 initial begin #1000000;$fatal(1,"V24_GENERATOR_WATCHDOG");end
endmodule
