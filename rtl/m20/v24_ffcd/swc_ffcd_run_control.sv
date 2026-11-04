`timescale 1ns/1ps
// FPGA-only coordinator; not part of the external 20-MUX generator BOM.
module swc_ffcd_run_control #(
 parameter integer PARK_GUARD_TICKS=4
)(input wire sys_clk,reset,cpu_reset,run_request,stop_request,step_request,
 input wire control_window,ref_fall_ce,observe_ce,
 output logic safe_hold=1,parked=1,cycle_active=0,step_ack=0,
 output wire step_ready,
 output logic [2:0] control_state=0);
 localparam IDLE=0,ARM=1,ACTIVE=2,CLOSING=3;
 logic pending_step=0,previous_step=0,single=0,stop_pending=0,completed=0;
 integer guard_count=0;
 assign step_ready=(control_state==IDLE)&&!pending_step&&!cpu_reset&&!stop_request;
 always_ff @(posedge sys_clk)begin
  previous_step<=step_request;step_ack<=0;
  if(reset)begin
   safe_hold<=1;parked<=1;cycle_active<=0;control_state<=IDLE;pending_step<=0;
   previous_step<=0;single<=0;stop_pending<=0;completed<=0;guard_count<=0;
  end else begin
   if(stop_request || cpu_reset)pending_step<=0;
   else if(step_ready && step_request&&!previous_step)pending_step<=1;
   case(control_state)
    IDLE:begin
     if(control_window && !stop_request && (run_request || pending_step))begin
      safe_hold<=0;parked<=0;single<=!run_request;pending_step<=0;
      stop_pending<=0;completed<=0;control_state<=ARM;
     end
    end
    ARM:begin
     if(stop_request || !run_request)stop_pending<=1;
     if(ref_fall_ce)begin cycle_active<=1;control_state<=ACTIVE;end
    end
    ACTIVE:begin
     if(stop_request || !run_request)stop_pending<=1;
     if(observe_ce)completed<=1;
     if(control_window && completed && (single || stop_pending || stop_request || !run_request))begin
      safe_hold<=1;cycle_active<=0;guard_count<=PARK_GUARD_TICKS;control_state<=CLOSING;
     end
    end
    CLOSING:begin
     if(guard_count==1)begin parked<=1;control_state<=IDLE;step_ack<=single;end
     else guard_count<=guard_count-1;
    end
    default:begin safe_hold<=1;cycle_active<=0;parked<=1;control_state<=IDLE;end
   endcase
  end
 end
endmodule
