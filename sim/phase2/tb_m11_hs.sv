`timescale 1ns/1ps
module tb_m11_hs #(
 parameter integer Q_PHASE=4,QM_PHASE=12,FAULT=0,FREQUENCY_HZ=25000000,PATTERN=5,
 parameter integer TEST_BITS=64,REQUIRE_ZERO=0,
 parameter realtime MASTER_NS=2.0,SLAVE_NS=3.0
);
 reg clk=0;always #10 clk=~clk;
 wire tx,d,c,l0,l1,g,y,r;reg master,slave;
 wire raw_q=slave^(FAULT==1 || FAULT==3);
 wire raw_m=master^(FAULT==2 || FAULT==3);
 // External ideal transparent latches with independent delayed assignments.
 always @(d or c) if(!c) master<=#(MASTER_NS) d;
 always @(master or c) if(c) slave<=#(SLAVE_NS) master;
 function integer mult(input integer hz);
   case(hz) 5000000:mult=12;75000000,150000000,200000000:mult=24;
   125000000:mult=20;default:mult=16;endcase
 endfunction
 function integer divide(input integer hz);
   case(hz) 5000000:divide=120;10000000:divide=80;25000000:divide=32;
   50000000,75000000:divide=16;100000000,125000000,150000000:divide=8;
   200000000:divide=6;default:divide=32;endcase
 endfunction
 swcell_m11_hs_top #(.FREQUENCY_HZ(FREQUENCY_HZ),
   .MULT(mult(FREQUENCY_HZ)),.DIVIDE(divide(FREQUENCY_HZ)),
   .Q_PHASE(Q_PHASE),.QM_PHASE(QM_PHASE),.PATTERN(PATTERN),.BITS(64'(TEST_BITS)),
   .UART_BAUD(6250000),.POR_CYCLES(16),.TIMEOUT_CYCLES(5000000)) dut(
   .sys_clk(clk),.UART_RXD(1'b1),.UART_TX(tx),.LED_G(g),.LED_Y(y),.LED_R(r),
   .M11_DL_D(l0),.M11_DL_EN(l1),.M11_DL_Q(1'b0),
   .M11_DFF_D(d),.M11_DFF_CLK(c),.M11_DFF_Q(raw_q),.M11_DFF_QM(raw_m));
 integer fd,b,bytes=0;reg [7:0] data;string filename;
 // 50MHz / 6.25M UART = 8 clocks per bit, serial framing checked independently.
 realtime last_rise=0,delta;
 always @(posedge c) begin
   if(last_rise>0 && !dut.stop && dut.engine.run) begin
     delta=$realtime-last_rise;
     if(delta<1.0e9/FREQUENCY_HZ-0.02 || delta>1.0e9/FREQUENCY_HZ+0.02)
       $fatal(1,"Wrong generated CLK period %f",delta);
   end
   last_rise=$realtime;
 end
 always @(d) if(dut.engine.reset_n && dut.engine.run && !dut.stop && dut.engine.advancing && last_rise>0) begin
   delta=$realtime-last_rise;
   if(FREQUENCY_HZ==1000000) begin
     // Low CLK uses an ordinary output FF; UNISIM adds 100ps on the D ODDR.
     if(delta<259.8 || delta>260.2) $fatal(1,"Low-frequency D phase %f",delta);
   end else if(delta<2.5e8/FREQUENCY_HZ-0.02 || delta>2.5e8/FREQUENCY_HZ+0.02)
     $fatal(1,"D/CLK phase mismatch %f",delta);
 end
 generate if(FAULT==4) begin
   initial begin wait(dut.engine.q_lane.total_bits==16);force dut.clocks.g_mmcm.lock=0;end
 end else if(FAULT==5) begin
   initial begin
     wait(dut.engine.q_lane.total_bits==16);force dut.engine.reset_n=0;
     #200;release dut.engine.reset_n;
   end
 end endgenerate
 initial begin
   if(!$value$plusargs("OUTPUT=%s",filename)) filename="hs.jsonl";
   fd=$fopen(filename,"w");if(!fd) $fatal(1,"Cannot open output");
   forever begin
     @(negedge tx);#80;if(tx!==0) $fatal(1,"Start bit");
     for(b=0;b<8;b=b+1) begin #160;data[b]=tx;end
     #160;if(tx!==1) $fatal(1,"Stop bit");
     $fwrite(fd,"%c",data);bytes=bytes+1;
   end
 end
 // Independent polynomial evaluator (integer bit positions, not DUT state).
 reg [30:0] golden=31'h13579bdf;
 reg [2:0] index=0;
 reg expected_data;integer i;reg [30:0] next_golden;
 always @(posedge dut.dc) begin
   if(dut.engine.dr) begin golden=31'h13579bdf;index=0;end
   else if(dut.dce && dut.engine.advancing) begin
     case(PATTERN)
       0:expected_data=0;1:expected_data=1;2:expected_data=index[0];
       3:expected_data=index[1];default:expected_data=golden[30];
     endcase
     if(dut.engine.bit_value!==expected_data || dut.engine.prbs!==golden)
       $fatal(1,"Independent stimulus/PRBS check failed");
     for(i=30;i>0;i=i-1) next_golden[i]=golden[i-1];
     next_golden[0]=golden[30]^golden[27];golden=next_golden;index=index+1'b1;
   end
 end
 initial begin
   wait(dut.state==9);#1000;$fclose(fd);
   if(FAULT==4) begin
     if(!dut.aborted) $fatal(1,"Clock loss must abort");
     $display("HS_SIM_PASS clock_loss=ABORTED");$finish;
   end
   if(dut.aborted || dut.qt!=TEST_BITS || dut.mt!=TEST_BITS) $fatal(1,"Incomplete run");
   if(FAULT==0 && (REQUIRE_ZERO || (Q_PHASE==4 && QM_PHASE==12)) && (dut.qe!=0 || dut.me!=0))
     $fatal(1,"Normal phases must pass qe=%d me=%d",dut.qe,dut.me);
   if(FAULT==1 && (dut.qe!=TEST_BITS || dut.me!=0)) $fatal(1,"Q injection count");
   if(FAULT==2 && (dut.me!=TEST_BITS || dut.qe!=0)) $fatal(1,"QM injection count");
   if(FAULT==3 && (dut.me!=TEST_BITS || dut.qe!=TEST_BITS)) $fatal(1,"Combined injection count");
   if((FAULT==1 || FAULT==3) && (dut.qf!=1 || dut.qx===dut.qa || dut.qs!==dut.qstart))
     $fatal(1,"Q first-error cycle/data/PRBS tag mismatch");
   if((FAULT==2 || FAULT==3) && (dut.mf!=1 || dut.mx===dut.ma || dut.ms!==dut.mstart))
     $fatal(1,"QM first-error cycle/data/PRBS tag mismatch");
   if(FAULT==0 && Q_PHASE==1 && dut.qe==0) $fatal(1,"Early Q sample must fail");
   if(FAULT==0 && QM_PHASE==8 && dut.me==0) $fatal(1,"Early QM sample must fail");
   $display("HS_SIM_PASS frequency=%d qphase=%d mphase=%d fault=%d qe=%d me=%d bytes=%d",FREQUENCY_HZ,Q_PHASE,QM_PHASE,FAULT,dut.qe,dut.me,bytes);
   $finish;
 end
 initial begin #100_000_000;$fatal(1,"HS timeout");end
endmodule
