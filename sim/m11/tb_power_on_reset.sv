`timescale 1ns/1ps
`default_nettype none
module tb_power_on_reset;
 reg clk=0;
 wire rst_one, rst_four;
 integer edge_number;
 swc_power_on_reset #(.HOLD_CYCLES(1)) one(.clk(clk),.rst(rst_one));
 swc_power_on_reset #(.HOLD_CYCLES(4)) four(.clk(clk),.rst(rst_four));
 initial begin
   // Configuration INIT must assert reset even before the user clock starts.
   #100;
   if(rst_one!==1 || rst_four!==1) $fatal(1,"POR must start asserted without an external reset");
   for(edge_number=1;edge_number<=12;edge_number=edge_number+1) begin
     #5;clk=1;
     #1;
     if(rst_one!==(edge_number<3)) $fatal(1,"HOLD_CYCLES=1 off-by-one");
     if(rst_four!==(edge_number<6)) $fatal(1,"HOLD_CYCLES=4 off-by-one");
     #4;clk=0;
   end
   // No run-time reset from a paused/restarted user clock.
   #100;
   if(rst_one!==0 || rst_four!==0) $fatal(1,"POR spuriously retriggered");
   $display("POWER_ON_RESET_PASS init=PASS hold=PASS release=PASS");
   $finish;
 end
 initial begin #1_000;$fatal(1,"POR timeout");end
endmodule
`default_nettype wire
