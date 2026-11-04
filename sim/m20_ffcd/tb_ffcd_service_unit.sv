`timescale 1ns/1ps
module tb_ffcd_service_unit;
 logic sys_clk=0,reset=1,cpu_reset=0,run_request=0,stop_request=0,step_request=0;
 always #10 sys_clk=~sys_clk;
 wire clk_ref,safe_hold,parked,active,ack,ready,rr,rf,rs,pv,wr,ob,ro,cw,cc,level;
 wire[15:0]age;wire[2:0]state;
 swc_ffcd_ref_div div(.sys_clk(sys_clk),.reset(reset),.clk_ref(clk_ref));
 swc_ffcd_service svc(.sys_clk(sys_clk),.reset(reset),.clk_ref(clk_ref),.cycle_active(active),.ref_rise_ce(rr),.ref_fall_ce(rf),.ram_sample_ce(rs),.preview_ce(pv),.write_ce(wr),.observe_ce(ob),.rom_read_ce(ro),.control_window(cw),.commit_clk(cc),.age(age),.ref_level(level));
 swc_ffcd_run_control ctrl(.sys_clk(sys_clk),.reset(reset),.cpu_reset(cpu_reset),.run_request(run_request),.stop_request(stop_request),.step_request(step_request),.control_window(cw),.ref_fall_ce(rf),.observe_ce(ob),.safe_hold(safe_hold),.parked(parked),.cycle_active(active),.step_ack(ack),.step_ready(ready),.control_state(state));
 logic[11:0]ra=0;wire[15:0]rd;
 logic[7:0]ma=0;logic[3:0]wd=0;wire[3:0]md;
 logic ce=0,oe=0,we=0,rst=0,prime=0;
 m20_ffcd_memory mem(.sys_clk(sys_clk),.rst(rst),.rom_read_ce(ro),.ram_sample_ce(rs),.commit_ce(pv),.write_ce(wr),.prime_rom(prime),.rom_addr(ra),.rom_data(rd),.ram_addr(ma),.ram_wdata(wd),.ram_rdata(md),.ram_ce(ce),.ram_oe(oe),.ram_we(we));
 integer checks=0,i,cycles=0,previews=0;
 always @(posedge sys_clk)begin if(ob)cycles=cycles+1;if(pv)previews=previews+1;end
 initial begin
  for(i=0;i<4096;i=i+1)mem.bram.rom[i]=i;
  for(i=0;i<256;i=i+1)mem.bram.memory[i]=i%16;
  repeat(3)@(posedge sys_clk);@(negedge sys_clk);reset=0;run_request=1;
  // ROM address is held across its two synchronous response clocks.
  ra=12'ha5;@(posedge sys_clk);while(!ro)@(posedge sys_clk);#1ps;ra=12'ha6;
  repeat(3)@(posedge sys_clk);#1ps;if(rd!==16'h00a5)$fatal(1,"FFCD_ROM_ADDRESS_NOT_HELD");checks=checks+1;
  // Same for RAM, then return to idle bus before the following transaction.
  @(negedge sys_clk);ce=1;oe=1;we=0;ma=8'h37;
  @(posedge sys_clk);while(!rs)@(posedge sys_clk);#1ps;ma=8'h38;
  repeat(3)@(posedge sys_clk);#1ps;if(md!==7)$fatal(1,"FFCD_RAM_ADDRESS_NOT_HELD");checks=checks+1;
  @(negedge sys_clk);oe=0;we=1;ma=8'h42;wd=5;
  @(posedge sys_clk);while(!rs)@(posedge sys_clk);#1ps;if(!mem.pending_write)$fatal(1,"FFCD_NO_PENDING");
  @(negedge sys_clk);ma=8'h43;wd=6;rst=1;
  @(posedge sys_clk);while(!wr)@(posedge sys_clk);#1ps;
  if(mem.bram.memory[8'h42]!==2 || mem.write_count!=0)$fatal(1,"FFCD_ABORT_FAILED");checks=checks+1;
  @(negedge sys_clk);rst=0;
  @(posedge sys_clk);while(!rs)@(posedge sys_clk);#1ps;
  @(negedge sys_clk);ma=8'h44;wd=7;
  @(posedge sys_clk);while(!wr)@(posedge sys_clk);#1ps;
  if(mem.bram.memory[8'h43]!==6 || mem.write_count!=1)$fatal(1,"FFCD_WRITE_NOT_SNAPSHOT");checks=checks+1;
  @(negedge sys_clk);ce=0;we=0;run_request=0;stop_request=1;
  wait(parked);repeat(120)@(posedge sys_clk);#1ps;
  if(mem.write_count!=1 || mem.pending_write)$fatal(1,"FFCD_PARK_REPEATED_WRITE");checks=checks+1;
  if(cycles!=previews)$fatal(1,"FFCD_REF_MICROCYCLE_RATIO");checks=checks+1;
  $display("FFCD_SERVICE_UNIT_PASS checks=%0d bram_registered=1 held_addresses=1 reset_abort=1 single_write=1 cycles=%0d",checks,cycles);$finish;
 end
 initial begin #200000;$fatal(1,"FFCD_SERVICE_UNIT_WATCHDOG");end
endmodule
