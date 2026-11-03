`timescale 1ns/1ps
module tb_hs_controls;
 reg clk=0,rst=1,ce=1,stopped=0;
 always #5 clk=~clk;
 wire pin_data,advancing,bit_value,launched_data;
 wire [30:0] launched_state,sequence_state;
 swc_hs_pattern_driver driver(.clk(clk),.rst(rst),.ce(ce),.stopped(stopped),
   .pin_data(pin_data),.advancing(advancing),.bit_value(bit_value),
   .launched_data(launched_data),.launched_state(launched_state),.sequence_state(sequence_state));
 reg source_done=0;
 reg [255:0] source_payload=0;
 wire valid;wire [255:0] payload;
 swc_snapshot_bridge #(.WIDTH(256)) bridge(.clk(clk),.rst(rst),
   .source_done(source_done),.source_payload(source_payload),.valid(valid),.payload(payload));
 reg [30:0] held_state;reg held_pin;
 integer dest_edges;
 initial begin
   repeat(5) @(negedge clk);rst=0;
   wait(advancing);repeat(10) @(negedge clk);
   ce=0;held_state=sequence_state;held_pin=pin_data;
   repeat(8) begin
     @(negedge clk);
     if(sequence_state!==held_state || pin_data!==held_pin)
       $fatal(1,"CE pause changed PRBS or physical data output");
   end
   ce=1;stopped=1;
   repeat(8) begin
     @(negedge clk);
     if(sequence_state!==held_state || pin_data!==held_pin)
       $fatal(1,"Stopped driver changed PRBS or physical data output");
   end
   stopped=0;@(negedge clk);
   if(sequence_state!=={held_state[29:0],held_state[30]^held_state[27]})
     $fatal(1,"Resume skipped or duplicated PRBS transaction");
   // Hold all payload bits before asserting done, asynchronous to destination.
   #2;source_payload=256'h123456789abcdef0_ffffffff00000001_0000000100000002_a55af00f12345678;
   #1;source_done=1;dest_edges=0;
   while(!valid) begin
     @(posedge clk);#0.2;dest_edges=dest_edges+1;
     if(dest_edges<4 && valid) $fatal(1,"Snapshot captured before synchronizer/settling interval");
     if(dest_edges>7) $fatal(1,"Snapshot handshake timeout");
   end
   if(payload!==source_payload) $fatal(1,"Bundled 256-bit snapshot was torn");
   source_payload=~source_payload;
   repeat(5) @(negedge clk);
   if(payload!==~source_payload) $fatal(1,"Completed snapshot changed");
   rst=1;source_done=0;@(negedge clk);rst=0;
   if(valid || payload!==0) $fatal(1,"Snapshot reset failed");
   #3;source_payload=256'hfedcba9876543210_00000001ffffffff_00000000ffffffff_55aa0ff012345678;
   #2;source_done=1;wait(valid);#0.2;
   if(payload!==source_payload) $fatal(1,"Second snapshot after reset failed");
   $display("HS_CONTROLS_SIM_PASS ce_pause=PASS stop_resume=PASS snapshot256=PASS reset=PASS");
   $finish;
 end
 initial begin #10000;$fatal(1,"Controls timeout");end
endmodule
