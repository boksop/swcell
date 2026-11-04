`timescale 1ns/1ps
// Local path experiment only: no CPU FSM execution or ROM program advancement.
module tb_ff16_cpu_cones;
 logic c=0,park=1,initializing=1;
 real dr[0:19],df[0:19],sr[0:19],sf[0:19],td=1.0,chain_stage=2.0;
 wire h,s,hs,ss,hd,sd,qs,qms,qd,qmd,mes,ses,med,sed;
 wire[32:0] qvec,dvec;
 logic[32:0] old_vec;
 logic[15:0] rom;
 logic[5:0] keys;
 logic[3:0] ram;
 integer src,dst,id,nextsrc,expectdst,fd,rf,scan,count=0,mismatches=0;
 integer speed,delay_idx;
 string dir;
 wire srcd=initializing?old_vec[src]:nextsrc[0];
 wire dstd=initializing?old_vec[dst]:dvec[dst];
 for(genvar k=0;k<33;k=k+1)assign qvec[k]=(k==src)?qs:((k==dst)?qd:old_vec[k]);
 swc_ff16_phase_timing #(.TAP_STAGES(16)) gen(.clk_ref(c),.safe_hold(park),.dr(dr),.df(df),.sr(sr),.sf(sf),.master_hold(h),.slave_open(s),.delayed_ref(),.tap4(),.tap8(),.tap12(),.tap16(),.h_raw(),.s_raw());
 swc_ff16_path_delay bs_h(.a(h),.rise_ns(1.0),.fall_ns(1.0),.y(hs));
 swc_ff16_path_delay bs_s(.a(s),.rise_ns(1.0),.fall_ns(1.0),.y(ss));
 swc_ff16_path_delay bd_h(.a(h),.rise_ns(4.0),.fall_ns(4.0),.y(hd));
 swc_ff16_path_delay bd_s(.a(s),.rise_ns(4.0),.fall_ns(4.0),.y(sd));
 swc_ff16_latch_pair source(.h(hs),.s(ss),.d(srcd),.m_open(1.0),.m_close(1.0),.s_open(1.0),.s_close(1.0),.m_data_r(0.1),.m_data_f(0.1),.s_data_r(0.1),.s_data_f(0.1),.q(qs),.qm(qms),.me(mes),.se(ses));
 swc_ff16_latch_pair destination(.h(hd),.s(sd),.d(dstd),.m_open(5.0),.m_close(5.0),.s_open(5.0),.s_close(5.0),.m_data_r(0.1),.m_data_f(0.1),.s_data_r(0.1),.s_data_f(0.1),.q(qd),.qm(qmd),.me(med),.se(sed));
 ff16_frozen_cone cone(.qbits(qvec),.rom_data(rom),.keys(keys),.ram_rdata(ram),.rst(1'b0),.dt(td),.dbits(dvec));
 initial begin
  if(!$value$plusargs("REVIEW=%s",dir))$fatal(1,"REVIEW path required");
  rf=$fopen({dir,"/cone_results.csv"},"w");
  $fwrite(rf,"path_id,chain_stage_ns,cell_min_ns,expected_destination,actual_destination,actual_master,mismatch\n");
  for(speed=0;speed<2;speed=speed+1)begin
   chain_stage=(speed==0)?2.0:0.5;
   for(delay_idx=0;delay_idx<4;delay_idx=delay_idx+1)begin
    case(delay_idx)0:td=0.125;1:td=0.25;2:td=0.5;3:td=1.0;endcase
    fd=$fopen({dir,"/cone_vectors.txt"},"r");if(!fd)$fatal(1,"vectors missing");
    while(!$feof(fd))begin
     park=1;c=0;initializing=1;#100;
     scan=$fscanf(fd,"%d %d %d %h %d %d %h %h %h\n",id,src,dst,old_vec,nextsrc,expectdst,rom,keys,ram);
     if(scan==9)begin
      for(integer i=0;i<20;i=i+1)begin dr[i]=(i<16)?chain_stage:1.0;df[i]=dr[i];sr[i]=1.0;sf[i]=1.0;end
      sr[16]=4.0;sf[17]=4.0;#100;
      park=0;#1000;repeat(2)begin c=1;#1000;c=0;#1000;end
      if(qs!==old_vec[src] || qd!==old_vec[dst])$fatal(1,"CONE_INIT id=%0d",id);
      initializing=0;#500;
      if(dvec[dst]!==expectdst[0] || qmd!==expectdst[0])$fatal(1,"CONE_ALIGNMENT id=%0d",id);
      c=1;#500;
      if(qs!==nextsrc[0])$fatal(1,"SOURCE_NOT_LAUNCHED id=%0d",id);
      $fwrite(rf,"%0d,%0.3f,%0.3f,%0d,%b,%b,%0d\n",id,chain_stage,td,expectdst,qd,qmd,qd!==expectdst[0]);
      if(qd!==expectdst[0])mismatches=mismatches+1;
      count=count+1;
     end
    end
    $fclose(fd);
   end
  end
  $fclose(rf);$display("FF16_CPU_CONES_COMPLETE cases=%0d observed_mismatches=%0d no_full_CPU=1",count,mismatches);$finish;
 end
 initial begin #20000000;$fatal(1,"CONE_WATCHDOG");end
endmodule
