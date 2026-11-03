`timescale 1ns/1ps
`default_nettype none
// Decode physical UART waveforms at the real board clock and baud rate.
module swc_pin_id_checker #(parameter integer IS_W23=0)(
 input wire tx, rst, output reg done);
 localparam integer BIT_NS=8680;
 integer n,bit_no;
 reg [7:0] received,expected;
 realtime previous_line_end;
 initial begin
   done=0;
   wait(rst===0);
   for(n=0;n<15;n=n+1) begin
     @(negedge tx);
     if(n>0 && n%5==0 && $realtime-previous_line_end<100_000)
       $fatal(1,"Pin-ID repetition idle gap too short");
     #(BIT_NS/2);
     if(tx!==0) $fatal(1,"Pin-ID UART start bit");
     for(bit_no=0;bit_no<8;bit_no=bit_no+1) begin
       #(BIT_NS);received[bit_no]=tx;
     end
     #(BIT_NS);
     if(tx!==1) $fatal(1,"Pin-ID UART stop bit");
     case(n%5)
       0:expected=IS_W23?8'h57:8'h56;
       1:expected=8'h32;
       2:expected=IS_W23?8'h33:8'h30;
       3:expected=8'h0d;
       default:expected=8'h0a;
     endcase
     if(received!==expected)
       $fatal(1,"Pin-ID channel W23=%0d byte %0d: got %02x expected %02x",IS_W23,n,received,expected);
     if(n%5==4) previous_line_end=$realtime;
   end
   done=1;
 end
endmodule

module tb_uart_pin_id;
 reg clk=0;
 wire v20,w23,done_v20,done_w23;
 wire g,y,r,dl_d,dl_en,dff_d,dff_clk;
 always #10 clk=~clk;
 swcell_uart_pin_id_top #(.POR_CYCLES(16),.GAP_CYCLES(5000)) dut(
   .sys_clk(clk),.PIN_V20_TX(v20),.PIN_W23_TX(w23),
   .LED_G(g),.LED_Y(y),.LED_R(r),.M11_DL_D(dl_d),.M11_DL_EN(dl_en),
   .M11_DFF_D(dff_d),.M11_DFF_CLK(dff_clk));
 swc_pin_id_checker #(.IS_W23(0)) check_v20(.tx(v20),.rst(dut.rst),.done(done_v20));
 swc_pin_id_checker #(.IS_W23(1)) check_w23(.tx(w23),.rst(dut.rst),.done(done_w23));
 initial begin
   wait(done_v20 && done_w23);
   if({dl_d,dl_en,dff_d,dff_clk}!==4'b0100 || y!==1 || r!==0)
     $fatal(1,"Pin-ID safe outputs / LEDs failed");
   $display("UART_PIN_ID_SIM_PASS clock=50000000 baud=115200 V20=V20 W23=W23 lines_per_pin=3 bytes_per_pin=15");
   $finish;
 end
 initial begin #5_000_000;$fatal(1,"Pin-ID simulation timeout");end
endmodule
`default_nettype wire
