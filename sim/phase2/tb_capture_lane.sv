`timescale 1ns/1ps
module tb_capture_lane;
 reg clk=0,rst=1,enable=0,ce=0,actual=0,expected=0;
 always #5 clk=~clk;
 wire done;wire [63:0] total,errors,first;wire x,a,event_error;wire [30:0] fs,ss;
 swc_capture_lane #(.LIMIT(64'h100000002)) dut(.clk(clk),.rst(rst),.enable(enable),
   .sample_ce(ce),.actual(actual),.expected(expected),.expected_state(31'h123),
   .done(done),.total_bits(total),.errors(errors),.first_cycle(first),
   .first_expected(x),.first_actual(a),.first_state(fs),.start_state(ss),.error_event(event_error));
 initial begin
   repeat(4) @(negedge clk);rst=0;enable=1;ce=1;
   // Reach the 32-bit rollover boundary directly; exercise the real 64-bit adder.
   dut.issued=64'hfffffffe;dut.total_bits=64'hfffffffe;
   dut.errors=64'hfffffffe;actual=1;
   wait(done);@(negedge clk);
   if(total!=64'h100000002 || errors!=64'h100000002) $fatal(1,"64-bit carry failed");
   repeat(5) @(negedge clk);
   if(total!=64'h100000002) $fatal(1,"Count did not freeze");
   rst=1;@(negedge clk);rst=0;enable=0;
   repeat(3) @(negedge clk);
   if(total!=0 || errors!=0 || done) $fatal(1,"Reset/disabled counting failed");
   $display("CAPTURE64_SIM_PASS carry=PASS freeze=PASS reset=PASS");$finish;
 end
 initial begin #10000;$fatal(1,"Counter timeout");end
endmodule
