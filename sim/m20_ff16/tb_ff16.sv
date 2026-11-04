`timescale 1ns/1ps
module ff16_test_runner #(parameter integer TAP_STAGES=8);
 logic clk_ref=0,safe_hold=1,data_drive=0,pipe_enable=1,checking=0,trace_on=0;
 wire h,s,cd,tap4,tap8,tap12,tap16,hr,srraw;
 real dr[0:19],df[0:19],sr[0:19],sf[0:19];
 real bmr[0:32],bmf[0:32],bsr[0:32],bsf[0:32];
 real mo[0:32],mc[0:32],so[0:32],sc[0:32];
 real mdr[0:32],mdf[0:32],sdr[0:32],sdf[0:32];
 wire [32:0] q,qm,me,se,hl,sl,d;
 assign d[31:0]={32{data_drive}};
 assign #(0.1,0.1)d[32]=pipe_enable?q[0]:data_drive;
 swc_ff16_phase_timing #(.TAP_STAGES(TAP_STAGES)) gen(.clk_ref(clk_ref),.safe_hold(safe_hold),.dr(dr),.df(df),.sr(sr),.sf(sf),.master_hold(h),.slave_open(s),.delayed_ref(cd),.tap4(tap4),.tap8(tap8),.tap12(tap12),.tap16(tap16),.h_raw(hr),.s_raw(srraw));
 for(genvar n=0;n<33;n=n+1)begin:g_leaf
  swc_ff16_path_delay mh(.a(h),.rise_ns(bmr[n]),.fall_ns(bmf[n]),.y(hl[n]));
  swc_ff16_path_delay sh(.a(s),.rise_ns(bsr[n]),.fall_ns(bsf[n]),.y(sl[n]));
  swc_ff16_latch_pair ff(.h(hl[n]),.s(sl[n]),.d(d[n]),.m_open(mo[n]),.m_close(mc[n]),.s_open(so[n]),.s_close(sc[n]),.m_data_r(mdr[n]),.m_data_f(mdf[n]),.s_data_r(sdr[n]),.s_data_f(sdf[n]),.q(q[n]),.qm(qm[n]),.me(me[n]),.se(se[n]));
 end
 string root_dir,id,config_path,trace_path;
 integer manifest,cf,rf,tf,ef,scan,i,c,mode,kind=0,global_overlap_events,own_overlap_events,data_errors,pipe_errors,penetration,missing_windows;
 integer cases=0,guard_fail,unsafe_windows;integer first_master,first_slave,d2_master,d2_slave;logic last_global=0,last_own=0;
 real high_ns,low_ns,jitter_ns,guard_ns,attack_ns,earliest,latest,d1_min,d2_min,last_edge;
 real close_time[0:32],open_time[0:32],m_started[0:32];real min_master_window;
 logic [32:0] old_me,old_se;logic old_q0,attack_armed=0;
 logic exp0,exppipe;logic [32:0]hold_q;
 task reset_measure(input integer direction);
  begin kind=direction;last_edge=$realtime;for(i=0;i<33;i=i+1)begin close_time[i]=-1;open_time[i]=-1;end end
 endtask
 always @(me or se)begin
  for(integer j=0;j<33;j=j+1)begin
   if(old_me[j]===1 && me[j]===0)m_started[j]=$realtime;
   if(checking && old_me[j]===0 && me[j]===1 && m_started[j]>=0)begin
    if($realtime-m_started[j]<min_master_window)min_master_window=$realtime-m_started[j];
    if($realtime-m_started[j]<100)unsafe_windows=unsafe_windows+1;
   end
  end
  if(checking)begin
   for(integer j=0;j<33;j=j+1)begin
    if(kind==1 && old_me[j]===0 && me[j]===1)close_time[j]=$realtime;
    if(kind==1 && old_se[j]===0 && se[j]===1)open_time[j]=$realtime;
    if(kind==2 && old_se[j]===1 && se[j]===0)close_time[j]=$realtime;
    if(kind==2 && old_me[j]===1 && me[j]===0)open_time[j]=$realtime;
   end
   if(!$isunknown({me,se}))begin
    if(me!={33{1'b1}} && se!=0)begin if(!last_global)global_overlap_events=global_overlap_events+1;last_global=1;end else last_global=0;
    if(((~me)&se)!=0)begin if(!last_own)own_overlap_events=own_overlap_events+1;last_own=1;end else last_own=0;
   end
  end
  old_me=me;old_se=se;
 end
 always @(q[0])begin
  if(checking && q[0]!==old_q0 && !$isunknown(q[0]))begin
   if(mode==1 && kind==1 && attack_armed && me[0]===0 && se[0]===1)penetration=penetration+1;
   if(mode==2 && kind==2 && attack_armed && me[0]===0 && se[0]===1)penetration=penetration+1;
  end
  old_q0=q[0];
 end
 always @(clk_ref or safe_hold or h or s or cd or me or se or q or qm)begin
  #1ps;
  if(trace_on)$fwrite(tf,"%0.3f,%b,%b,%b,%b,%b,%h,%h,%h,%h,%b,%0d,%0d\n",$realtime,clk_ref,safe_hold,h,s,cd,me,se,qm,q,checking,kind,c);
 end
 task finish_measure(input integer direction);
  real a,b;integer ai,bi;bit complete;
  begin
   a=1e30;b=-1;complete=1;ai=-1;bi=-1;
   for(integer j=0;j<33;j=j+1)begin
    if(open_time[j]<0 || close_time[j]<0)complete=0;
    if(open_time[j]>=0 && open_time[j]<a)begin a=open_time[j];ai=j;end
    if(close_time[j]>b)begin b=close_time[j];bi=j;end
   end
   if(!complete)missing_windows=missing_windows+1;
   else begin
    if(direction==1 && a-b<d1_min)begin d1_min=a-b;first_master=bi;first_slave=ai;end
    if(direction==2 && a-b<d2_min)begin d2_min=a-b;d2_master=ai;d2_slave=bi;end
   end
   kind=0;
  end
 endtask
 task load_config;
  begin
   cf=$fopen(config_path,"r");if(!cf)$fatal(1,"FF16_CONFIG_MISSING");
   scan=$fscanf(cf,"%d %f %f %f %f\n",mode,high_ns,low_ns,jitter_ns,guard_ns);if(scan!=5)$fatal(1,"FF16_CONFIG_HEADER");
   for(i=0;i<20;i=i+1)begin scan=$fscanf(cf,"%f %f %f %f\n",dr[i],df[i],sr[i],sf[i]);if(scan!=4)$fatal(1,"FF16_CONFIG_GATE");end
   for(i=0;i<33;i=i+1)begin
    scan=$fscanf(cf,"%f %f %f %f %f %f %f %f %f %f %f %f\n",bmr[i],bmf[i],bsr[i],bsf[i],mo[i],mc[i],so[i],sc[i],mdr[i],mdf[i],sdr[i],sdf[i]);
    if(scan!=12)$fatal(1,"FF16_CONFIG_LEAF");
   end
   $fclose(cf);
  end
 endtask
 task rise_and_check(input real duration);
  real master_close,slave_open;
  begin
   exp0=data_drive;exppipe=q[0];reset_measure(1);clk_ref=1;
   if(mode==1)begin
    slave_open=0;for(integer a=0;a<TAP_STAGES;a=a+1)slave_open=slave_open+dr[a];
    slave_open=slave_open+dr[17]+dr[19]+bsr[0]+so[0];
    master_close=sr[16]+dr[18]+bmr[0]+mc[0];
    attack_ns=(master_close+slave_open)/2;
    if(master_close>slave_open+0.5 && attack_ns<duration)begin #(attack_ns);attack_armed=1;data_drive=~exp0;#(duration-attack_ns);end else #(duration);
   end else #(duration);
   finish_measure(1);attack_armed=0;
   if(q[31:0]!=={32{exp0}} || (!pipe_enable && q[32]!==exp0))begin data_errors=data_errors+1;$fwrite(ef,"%0.3f,rise_data,%0d,%b,%b,%h,%h\n",$realtime,c,exp0,q[0],qm,q);end
   if(pipe_enable && q[32]!==exppipe)begin pipe_errors=pipe_errors+1;$fwrite(ef,"%0.3f,pipeline,%0d,%b,%b,%h,%h\n",$realtime,c,exppipe,q[32],qm,q);end
  end
 endtask
 task fall_and_check(input real duration);
  real master_open,slave_close;
  begin
   hold_q=q;reset_measure(2);clk_ref=0;
   if(mode==2)begin
    master_open=0;for(integer a=0;a<TAP_STAGES;a=a+1)master_open=master_open+df[a];
    master_open=master_open+df[16]+df[18]+bmf[0]+mo[0];
    slave_close=sf[17]+df[19]+bsf[0]+sc[0];attack_ns=(master_open+slave_close)/2;
    if(slave_close>master_open+0.5 && attack_ns<duration)begin #(attack_ns);attack_armed=1;data_drive=~data_drive;#(duration-attack_ns);end else #(duration);
   end else begin
    // A low-phase D change is legal only after old Slave close, well before next rise.
    if(duration>220)begin #200;data_drive=~data_drive;#(duration-200);end else #(duration);
   end
   finish_measure(2);attack_armed=0;if(q!==hold_q)begin data_errors=data_errors+1;$fwrite(ef,"%0.3f,low_hold,%0d,%h,%h,%h,%h\n",$realtime,c,hold_q,q,qm,q);end
  end
 endtask
 task park_resume;
  begin
   // Normal hold after a settled Slave phase; C=Cd=1. No need to catch short dead zone.
   #100;safe_hold=1;#100;hold_q=q;
   if(h!==1 || s!==0 || me!=={33{1'b1}} || se!==0)$fatal(1,"FF16_SAFE_PARK_NOT_REACHED");
   clk_ref=0;#500;data_drive=~data_drive;clk_ref=1;#500;
   if(q!==hold_q)$fatal(1,"FF16_PARK_STATE_CHANGED");
   safe_hold=0;#100;
   if(q!==hold_q)$fatal(1,"FF16_RESUME_FALSE_UPDATE");
  end
 endtask
 initial begin
  if(!$value$plusargs("CASES=%s",root_dir))$fatal(1,"FF16_CASES_REQUIRED");
  manifest=$fopen({root_dir,"/cases.txt"},"r");if(!manifest)$fatal(1,"FF16_MANIFEST_MISSING");
  rf=$fopen({root_dir,"/results_tap",$sformatf("%0d",TAP_STAGES),".csv"},"w");
  $fwrite(rf,"case,tap,d1_ns,d2_ns,global_overlap_events,own_overlap_events,data_errors,pipeline_errors,penetration_events,missing_windows,guard_fail,master_index,slave_index,min_master_window_ns,short_master_windows,d2_master_index,d2_slave_index\n");
  while(!$feof(manifest))begin
   scan=$fscanf(manifest,"%s %s\n",id,config_path);
   if(scan==2)begin
    checking=0;trace_on=0;safe_hold=1;clk_ref=0;data_drive=0;pipe_enable=0;#200;
    load_config();#300;
    trace_path={root_dir,"/",id,"_tap",$sformatf("%0d",TAP_STAGES),".trace.csv"};tf=$fopen(trace_path,"w");
    $fwrite(tf,"time_ns,clk_ref,safe_hold,master_hold,slave_open,cd,master_effective,slave_effective,qm,q,checking,measurement_kind,reference_cycle\n");trace_on=1;
    ef=$fopen({root_dir,"/",id,"_tap",$sformatf("%0d",TAP_STAGES),".errors.csv"},"w");$fwrite(ef,"time_ns,type,reference_cycle,expected,actual,qm,q\n");
    safe_hold=0;#2000;repeat(2)begin clk_ref=1;#2000;clk_ref=0;#2000;end
    if(q!==0 || qm!==0)$fatal(1,"FF16_INITIALIZATION_UNKNOWN case=%s",id);
    global_overlap_events=0;own_overlap_events=0;data_errors=0;pipe_errors=0;penetration=0;missing_windows=0;guard_fail=0;unsafe_windows=0;
    d1_min=1e30;d2_min=1e30;first_master=-1;first_slave=-1;d2_master=-1;d2_slave=-1;last_global=0;last_own=0;
    min_master_window=1e30;attack_armed=0;
    pipe_enable=(mode!=1 && mode!=2);
    if(mode==4)begin safe_hold=1;#200;data_drive=1;#300;checking=1;safe_hold=0;#1;end
    else begin data_drive=(mode==1 || mode==2)?0:1;#300;checking=1;end
    for(c=0;c<4;c=c+1)begin
     rise_and_check(high_ns+((c%2)?jitter_ns:-jitter_ns));
     fall_and_check(low_ns+((c%3)?0:jitter_ns));
    end
    if(mode==3)begin rise_and_check(high_ns);park_resume();clk_ref=0;#500;data_drive=1;#300;checking=1;rise_and_check(high_ns);end
    checking=0;kind=0;safe_hold=1;#100;trace_on=0;$fclose(tf);$fclose(ef);
    if(d1_min<guard_ns || d2_min<guard_ns || missing_windows>0 || unsafe_windows>0)guard_fail=1;
    $fwrite(rf,"%s,%0d,%0.6f,%0.6f,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0.6f,%0d,%0d,%0d\n",id,TAP_STAGES,d1_min,d2_min,global_overlap_events,own_overlap_events,data_errors,pipe_errors,penetration,missing_windows,guard_fail,first_master,first_slave,min_master_window,unsafe_windows,d2_master,d2_slave);
    $display("FF16_CASE case=%s tap=%0d D1=%0.3f D2=%0.3f global=%0d own=%0d data=%0d pipe=%0d penetration=%0d missing=%0d",id,TAP_STAGES,d1_min,d2_min,global_overlap_events,own_overlap_events,data_errors,pipe_errors,penetration,missing_windows);
    cases=cases+1;
   end
  end
  $fclose(rf);$fclose(manifest);$display("FF16_SMALL_COMPLETE tap=%0d cases=%0d",TAP_STAGES,cases);$finish;
 end
 initial begin #10000000;$fatal(1,"FF16_WATCHDOG");end
endmodule
module tb_ff16_tap4;ff16_test_runner #(.TAP_STAGES(4))u();endmodule
module tb_ff16_tap8;ff16_test_runner #(.TAP_STAGES(8))u();endmodule
module tb_ff16_tap12;ff16_test_runner #(.TAP_STAGES(12))u();endmodule
module tb_ff16_tap16;ff16_test_runner #(.TAP_STAGES(16))u();endmodule
