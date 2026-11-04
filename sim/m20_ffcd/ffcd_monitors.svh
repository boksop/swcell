// Verification only. Do not synthesize timing observers or add them to CPU BOM.
real mclosed[0:32],sopened[0:32],sclosed[0:32],mopened[0:32];
bit rise_armed=0,fall_armed=0;
real d1_min=1e9,d2_min=1e9;
integer d1_checks=0,d2_checks=0;
integer event_file=0;string event_path;
initial if($value$plusargs("EVENT_LOG=%s",event_path))begin
 event_file=$fopen(event_path,"w");$fwrite(event_file,"time_ns,ref,safe_hold,H,S,age,control,ram_sample,preview,write,observe,rom_read,pc_hex,state_hex,ram_addr_hex,ram_data_hex,pending_write\n");
end
always @(posedge sys_clk)if(event_file)$fwrite(event_file,"%0.3f,%b,%b,%b,%b,%0d,%0d,%b,%b,%b,%b,%b,%h,%h,%h,%h,%b\n",$realtime,clk_ref,safe_hold,master_hold,slave_open,age,control_state,ram_sample_ce,commit_ce,write_ce,observe_ce,rom_read_ce,dbg_pc,dbg_state,ram_addr,ram_rdata,mem.pending_write);
always @(posedge clk_ref)begin
 rise_armed=checks_enable&&!safe_hold;
 for(integer j=0;j<33;j=j+1)begin mclosed[j]=-1;sopened[j]=-1;end
end
always @(negedge clk_ref)begin
 fall_armed=checks_enable&&!safe_hold;
 for(integer j=0;j<33;j=j+1)begin sclosed[j]=-1;mopened[j]=-1;end
end
for(genvar bitno=0;bitno<33;bitno=bitno+1)begin:g_clock_observer
 always @(posedge dut.state_me[bitno])if(rise_armed)mclosed[bitno]=$realtime;
 always @(posedge dut.state_se[bitno])if(rise_armed)sopened[bitno]=$realtime;
 always @(negedge dut.state_me[bitno])if(fall_armed)mopened[bitno]=$realtime;
 always @(negedge dut.state_se[bitno])if(fall_armed)sclosed[bitno]=$realtime;
end
always @(dut.state_me or dut.state_se)begin
 #1ps;
 if(checks_enable && ((~dut.state_me)!=0) && dut.state_se!=0)$fatal(1,"FFCD_GLOBAL_EFFECTIVE_OVERLAP");
end
always @(posedge sys_clk)if(checks_enable)begin:margin_measure
 real latest,earliest,delta;bit valid;
 if(rise_armed)begin
  latest=0;earliest=1e20;valid=1;
  for(integer j=0;j<33;j=j+1)begin
   if(mclosed[j]<0 || sopened[j]<0)valid=0;
   if(mclosed[j]>latest)latest=mclosed[j];if(sopened[j]>=0 && sopened[j]<earliest)earliest=sopened[j];
  end
  if(valid)begin delta=earliest-latest;if(delta<4.0)$fatal(1,"FFCD_D1_GUARD %0.3f",delta);if(delta<d1_min)d1_min=delta;d1_checks=d1_checks+1;rise_armed=0;end
 end
 if(fall_armed)begin
  latest=0;earliest=1e20;valid=1;
  for(integer j=0;j<33;j=j+1)begin
   if(sclosed[j]<0 || mopened[j]<0)valid=0;
   if(sclosed[j]>latest)latest=sclosed[j];if(mopened[j]>=0 && mopened[j]<earliest)earliest=mopened[j];
  end
  if(valid)begin delta=earliest-latest;if(delta<4.0)$fatal(1,"FFCD_D2_GUARD %0.3f",delta);if(delta<d2_min)d2_min=delta;d2_checks=d2_checks+1;fall_armed=0;end
 end
 if(parked && (!safe_hold || master_hold!==1 || slave_open!==0 || dut.state_me!=={33{1'b1}} || dut.state_se!==0))$fatal(1,"FFCD_PARK_ACK_NOT_SAFE");
end
final $display("FFCD_EFFECTIVE_MARGIN d1_ns=%0.3f d2_ns=%0.3f d1_checks=%0d d2_checks=%0d",d1_min,d2_min,d1_checks,d2_checks);
