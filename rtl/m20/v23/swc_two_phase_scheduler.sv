`timescale 1ns/1ps
// One system domain, registered phase pins. commit_clk is a reference-model observer only.
module swc_two_phase_scheduler #(
 parameter integer MASTER_TICKS=12,DEAD1_TICKS=4,SLAVE_TICKS=12,DEAD2_TICKS=4,
 parameter integer ROM_TICK=2,RAM_TICK=4,OBSERVE_TICK=2
)(input wire sys_clk,reset,run_enable,stop_request,step_request,
 output logic master_hold=1,slave_open=0,commit_clk=0,
 output wire commit_ce,rom_read_ce,ram_sample_ce,observe_ce,
 output logic parked=1,output logic [1:0] phase=3,output integer phase_tick=0);
 localparam M=0,D1=1,S=2,D2=3;
 logic single_cycle=0,stopping=0;
 assign commit_ce=!parked && phase==M && phase_tick==MASTER_TICKS-1;
 assign rom_read_ce=!parked && phase==S && phase_tick==ROM_TICK;
 assign ram_sample_ce=!parked && phase==M && phase_tick==RAM_TICK;
 assign observe_ce=!parked && phase==S && phase_tick==OBSERVE_TICK;
 initial begin
  if(MASTER_TICKS<2 || SLAVE_TICKS<2 || DEAD1_TICKS<0 || DEAD2_TICKS<0 || RAM_TICK>=MASTER_TICKS-1 || ROM_TICK>=SLAVE_TICKS || OBSERVE_TICK>=SLAVE_TICKS)
   $fatal(1,"invalid two-phase profile");
 end
 task finish_cycle;
  begin
   if(single_cycle || stopping || stop_request || !run_enable)begin parked<=1;phase<=D2;phase_tick<=0;end
   else begin phase<=M;phase_tick<=0;master_hold<=0;slave_open<=0;end
  end
 endtask
 always_ff @(posedge sys_clk)begin
  commit_clk<=0;
  if(reset)begin master_hold<=1;slave_open<=0;parked<=1;phase<=D2;phase_tick<=0;single_cycle<=0;stopping<=0;end
  else if(parked)begin
   master_hold<=1;slave_open<=0;
   if((run_enable && !stop_request) || step_request)begin
    parked<=0;single_cycle<=step_request;stopping<=0;phase<=M;phase_tick<=0;master_hold<=0;
   end
  end else begin
   if(stop_request || !run_enable)stopping<=1;
   phase_tick<=phase_tick+1;
   case(phase)
    M:if(phase_tick==MASTER_TICKS-1)begin
      master_hold<=1;commit_clk<=1;phase_tick<=0;
      if(DEAD1_TICKS==0)begin phase<=S;slave_open<=1;end else phase<=D1;
    end
    D1:if(phase_tick==DEAD1_TICKS-1)begin phase<=S;phase_tick<=0;slave_open<=1;end
    S:if(phase_tick==SLAVE_TICKS-1)begin
      slave_open<=0;phase_tick<=0;
      if(DEAD2_TICKS==0)finish_cycle();else phase<=D2;
    end
    D2:if(phase_tick==DEAD2_TICKS-1)finish_cycle();
   endcase
  end
 end
endmodule
