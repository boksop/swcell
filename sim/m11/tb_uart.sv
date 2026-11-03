`timescale 1ns/1ps
`default_nettype none
module tb_uart;
 localparam integer DIVISOR=868, BIT_NS=8680;
 reg clk=0,rst=1,valid=0,receiver_enabled=0;
 reg [7:0] data=0;
 wire ready,tx;
 integer received=0,i;
 reg [7:0] received_byte;
 always #5 clk=~clk;
 swc_uart_tx #(.CLK_HZ(100_000_000),.BAUD(115200)) dut(
   .clk(clk),.rst(rst),.data(data),.valid(valid),.ready(ready),.tx(tx));
 function automatic [7:0] expected_byte(input integer n);
   case(n) 0:expected_byte=8'h00;1:expected_byte=8'hff;
     2:expected_byte=8'ha5;default:expected_byte=8'h3c;endcase
 endfunction
 task automatic send(input [7:0] byte_value);
   begin
     @(negedge clk);
     while(!ready) @(negedge clk);
     data=byte_value;valid=1;
     @(negedge clk);valid=0;
   end
 endtask
 initial begin
   wait(receiver_enabled);
   forever begin
     @(negedge tx);
     #(BIT_NS/2);
     if(tx!==0) $fatal(1,"UART start bit");
     for(i=0;i<8;i=i+1) begin #(BIT_NS);received_byte[i]=tx;end
     #(BIT_NS);
     if(tx!==1 || received_byte!==expected_byte(received)) $fatal(1,"UART 115200 data/framing failure");
     received=received+1;
   end
 end
 initial begin
   repeat(4) @(negedge clk);
   rst=0;
   // Interrupt an in-flight frame; reset must restore idle and readiness.
   send(8'h55);
   repeat(20) @(negedge clk);
   rst=1;
   repeat(2) @(negedge clk);
   if(tx!==1 || ready!==1) $fatal(1,"UART reset recovery failed");
   rst=0;receiver_enabled=1;
   send(8'h00);send(8'hff);send(8'ha5);send(8'h3c);
   wait(received==4);
   wait(ready);
   $display("UART_UNIT_PASS baud=115200 divisor=%0d bytes=4 reset_recovery=PASS",DIVISOR);
   $finish;
 end
 initial begin #1_000_000;$fatal(1,"UART timeout");end
endmodule
`default_nettype wire
