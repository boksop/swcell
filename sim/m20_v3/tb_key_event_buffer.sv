`timescale 1ns/1ps
module tb_key_event_buffer;
 reg clk=0;always #10 clk=~clk;
 reg rst=1,sample_ce=0,read0_ack=0,read1_ack=0;
 reg[5:0] levels=0,press=0,consumed_keys=0;
 wire[5:0] keys;wire[3:0] queued;wire[9:0] overflows;
 swc_key_event_buffer dut(.*);
 task cycle;@(posedge clk);#1;@(negedge clk);endtask
 task tap(input[5:0] mask);
  levels=mask;press=mask;cycle();levels=0;press=0;cycle();
 endtask
 task consume0;
  sample_ce=1;consumed_keys=keys;cycle();sample_ce=0;read0_ack=1;cycle();read0_ack=0;cycle();
 endtask
 task clear;
  rst=1;sample_ce=0;read0_ack=0;read1_ack=0;levels=0;press=0;cycle();rst=0;cycle();
 endtask
 initial begin
  repeat(2)cycle();rst=0;cycle();
  tap(1);repeat(100)cycle();
  if(keys!=1||queued!=1)$fatal(1,"KEY_SHORT_TAP_NOT_RETAINED");
  consume0();if(keys!=0||queued!=0)$fatal(1,"KEY_NOT_CONSUMED_ONCE");
  // A press after the CPU sample must survive the old sample's acknowledgement.
  sample_ce=1;consumed_keys=0;cycle();sample_ce=0;tap(2);
  read0_ack=1;cycle();read0_ack=0;cycle();
  if(keys!=2||queued!=1)$fatal(1,"KEY_LATE_EVENT_LOST");
  consume0();if(queued!=0)$fatal(1,"KEY_LATE_EVENT_REPLAY");
  // Enqueue coincident with an empty-queue sample is already seen via levels.
  levels=4;press=4;sample_ce=1;consumed_keys=4;cycle();
  levels=0;press=0;sample_ce=0;read0_ack=1;cycle();read0_ack=0;cycle();
  if(queued!=0||keys!=0)$fatal(1,"KEY_SIMULTANEOUS_DUPLICATED");
  tap(1);tap(8);if(keys!=1||queued!=2)$fatal(1,"KEY_ORDER_HEAD");
  consume0();if(keys!=8)$fatal(1,"KEY_ORDER_SECOND");consume0();
  levels=4;press=4;cycle();press=0;consume0();
  if(keys!=4||queued!=0)$fatal(1,"KEY_HELD_LEVEL_LOST");
  levels=0;cycle();if(keys!=0)$fatal(1,"KEY_HELD_RELEASE");
  tap(32);if(keys!=32)$fatal(1,"ACTION_NOT_RETAINED");
  consume0();if(keys!=32)$fatal(1,"ACTION_WRONG_BANK_CONSUMED");
  consumed_keys=0;read1_ack=1;cycle();read1_ack=0;cycle();
  if(keys!=32)$fatal(1,"ACTION_LATE_EVENT_LOST");
  consumed_keys=32;read1_ack=1;cycle();read1_ack=0;cycle();
  if(keys!=0)$fatal(1,"ACTION_NOT_CONSUMED");
  for(integer i=0;i<8;i=i+1)tap(6'(1<<(i%4)));
  tap(8);if(queued!=8||overflows!=1)$fatal(1,"KEY_OVERFLOW_NOT_REPORTED");
  sample_ce=1;consumed_keys=keys;cycle();sample_ce=0;
  read0_ack=1;levels=4;press=4;cycle();read0_ack=0;levels=0;press=0;cycle();
  if(queued!=8||overflows!=1)$fatal(1,"KEY_SIMULTANEOUS_FULL_POP_PUSH");
  for(integer i=1;i<8;i=i+1)begin
   if(keys!=6'(1<<(i%4)))$fatal(1,"KEY_OVERFLOW_CORRUPTED_FIFO");consume0();
  end
  if(keys!=4)$fatal(1,"KEY_PUSH_AT_FULL_LOST");consume0();
  clear();if(queued||keys||overflows)$fatal(1,"KEY_RESET_FLUSH");
  $display("M20_V3_KEY_BUFFER_PASS short_tap=1 late_sample=1 coincident_sample=1 ordered=1 held=1 action_bank=1 overflow=1 simultaneous_full=1 reset=1");
  $finish;
 end
 initial begin #100000;$fatal(1,"KEY_BUFFER_TIMEOUT");end
endmodule
