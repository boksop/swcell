`timescale 1ns/1ps
`default_nettype none
module tb_m11 #(
 parameter integer CLK_HZ=100_000_000, BAUD=12_500_000,
 parameter integer STEP_NS=500, SYNC_STAGES=2
);
 localparam integer PATTERN=8, RANDOM=64;
 localparam realtime HALF_PERIOD_NS=5.0e8/CLK_HZ;
 localparam realtime BIT_NS=((CLK_HZ+BAUD/2)/BAUD)*1.0e9/CLK_HZ;
 localparam integer POR_CYCLES=16;
 reg clk=0;
 always #(HALF_PERIOD_NS) clk=~clk;
 wire dl_d,dl_en,dl_q,dff_d,dff_clk,dff_q,dff_qm,tx,done,passed,running,failed;
 assign done=dut.suite_done;
 wire model_dl,model_q,model_qm;
 integer fault_mode=0;
 wire fault_l=(fault_mode==1 && dut.engine.current_test==8'h07 && dut.engine.state==5);
 wire fault_q=(fault_mode==3 && dut.engine.current_test==8'h13 && dut.engine.state==5);
 wire fault_qm=((fault_mode==2 && dut.engine.current_test==8'h18) ||
                (fault_mode==3 && dut.engine.current_test==8'h13)) && dut.engine.state==5;
 assign dl_q=model_dl^fault_l;
 assign dff_q=model_q^fault_q;
 assign dff_qm=model_qm^fault_qm;
 swcell_fpga_top #(.CLK_HZ(CLK_HZ),.UART_BAUD(BAUD),
   .STEP_NS(STEP_NS),.SYNC_STAGES(SYNC_STAGES),.POR_CYCLES(POR_CYCLES),
   .PATTERN_STEPS(PATTERN),.RANDOM_STEPS(RANDOM)) dut(
   .sys_clk(clk),.UART_RXD(1'b1),.UART_TX(tx),
   .M11_DL_D(dl_d),.M11_DL_EN(dl_en),.M11_DL_Q(dl_q),
   .M11_DFF_D(dff_d),.M11_DFF_CLK(dff_clk),.M11_DFF_Q(dff_q),.M11_DFF_QM(dff_qm),
   .LED_G(passed),.LED_Y(running),.LED_R(failed));
 m11_behavioral_model model(.dl_d(dl_d),.dl_en(dl_en),.dl_q(model_dl),
   .dff_d(dff_d),.dff_clk(dff_clk),.dff_q(model_q),.dff_qm(model_qm));
 integer fd,scan_result,lines=0,characters=0;
 string output_file;
 reg [7:0] rx_byte;
 integer b;
 // Actual serial wire decoder: verifies framing, bit order and JSONL transport.
 initial begin
   if(!$value$plusargs("FAULT=%d",fault_mode)) fault_mode=0;
   if(!$value$plusargs("OUTPUT=%s",output_file)) output_file="uart.jsonl";
   fd=$fopen(output_file,"w");
   if(fd==0) $fatal(1,"Could not create UART output");
   forever begin
     @(negedge tx);
     #(BIT_NS/2);
     if(tx!==0) $fatal(1,"Invalid UART start bit");
     for(b=0;b<8;b=b+1) begin #(BIT_NS);rx_byte[b]=tx;end
     #(BIT_NS);
     if(tx!==1) $fatal(1,"Invalid UART stop bit");
     if(rx_byte==10) begin lines=lines+1;characters=0;end
     else begin
       if(characters==0 && rx_byte!="{") $fatal(1,"JSON line must start with brace");
       if(rx_byte<32 || rx_byte>126) $fatal(1,"Invalid UART ASCII byte");
       characters=characters+1;
     end
     $fwrite(fd,"%c",rx_byte);
   end
 end
 function automatic integer expected_count(input integer id);
   if(id<=5) expected_count=1;
   else if(id==8) expected_count=RANDOM;
   else if(id<17) expected_count=PATTERN;
   else if(id<=21) expected_count=3*PATTERN;
   else if(id==22) expected_count=3*RANDOM;
   else if(id==25) expected_count=PATTERN+1;
   else expected_count=PATTERN;
 endfunction
 function automatic integer fault_for(input integer id);
   fault_for=((fault_mode==1 && id==7) || (fault_mode==2 && id==24) ||
              (fault_mode==3 && id==19));
 endfunction
 localparam [63:0] PRBS_DATA=64'h26af37be27ad149e, PRBS_ENABLE=64'h9bdf13d68a4f1ac5;
 integer data_index;
 reg expected_data, expected_enable;
 // Independent stimulus assertions prevent a faulty/stuck pattern generator from
 // passing merely because both the physical model and reference saw the same D.
 task automatic verify_stimulus(input integer test_code, check_index);
   begin
     expected_data=0;expected_enable=1;
     if(test_code<17) begin
       case(test_code)
         1:expected_data=0;
         2:expected_data=1;
         3:begin expected_data=0;expected_enable=0;end
         4:begin expected_data=1;expected_enable=0;end
         5:expected_data=0;
         6:begin expected_data=check_index%2;expected_enable=0;end
         7:expected_data=check_index%2;
         8:begin expected_data=PRBS_DATA[63-check_index];expected_enable=PRBS_ENABLE[63-check_index];end
       endcase
       if(dl_d!==expected_data || dl_en!==expected_enable) $fatal(1,"Wrong latch stimulus");
     end else begin
       data_index=check_index/3;
       case(test_code)
         17:expected_data=0;
         18:expected_data=1;
         19:expected_data=data_index%2;
         20:expected_data=(data_index/2)%2;
         21:expected_data=(data_index/4)%2;
         22:expected_data=PRBS_DATA[63-data_index];
         23,24:expected_data=!(check_index%2);
         25:expected_data=(check_index>=PATTERN-1)?1:check_index%2;
       endcase
       if(dff_d!==expected_data) $fatal(1,"Wrong DFF data pattern test=%h index=%d",test_code,check_index);
       if(test_code<=22 && dff_clk!==(check_index%3!=1)) $fatal(1,"Wrong three-phase CLK");
       if(test_code==23 && dff_clk!==0) $fatal(1,"F07 CLK must stay low");
       if(test_code==24 && dff_clk!==1) $fatal(1,"F08 CLK must stay high");
       if(test_code==25 && dff_clk!==(check_index==PATTERN)) $fatal(1,"F09 last rising edge missing");
     end
   end
 endtask
 reg [63:0] checks=0, first_cycle=0;
 reg [3:0] first_inputs=0;
 reg [2:0] first_actual=0, first_expected=0, first_mask=0;
 integer id, results_seen=0, starts_seen=0, errors_seen=0, complete_seen=0;
 integer first_seen=0;
 reg [2:0] raw_expected, wanted_actual;
 always @(posedge clk) begin
   if(!dut.engine.rst) begin
     if(running!==!done || passed || failed) begin
       if(!done) $fatal(1,"Running LED status incorrect");
     end
     if(dut.engine.state==1) begin checks=0;first_seen=0;end
     if(dut.engine.apply && !dut.engine.step_ready) $fatal(1,"Invalid step handshake");
     if(dut.engine.check_valid) begin
       verify_stimulus(dut.engine.current_test,int'(checks));
       checks=checks+1;
       raw_expected={model_qm,model_q,model_dl};
       wanted_actual={dff_qm,dff_q,dl_q};
       if((dut.engine.expected & dut.engine.mask) !== (raw_expected & dut.engine.mask))
         $fatal(1,"Reference mismatch / one-cycle offset in test %h",dut.engine.current_test);
       if(dut.engine.actual !== wanted_actual) $fatal(1,"Insufficient synchronization settling");
       if(fault_for(dut.engine.current_test) && !first_seen) begin
         first_seen=1;first_cycle=dut.engine.cycles;
         first_inputs={dff_clk,dff_d,dl_en,dl_d};
         first_actual=wanted_actual;first_expected=raw_expected;first_mask=dut.engine.mask;
       end
     end
     if(dut.engine.message_valid && dut.engine.message_ready) begin
       id=dut.engine.current_test;
       case(dut.engine.event_type)
         0:starts_seen=starts_seen+1;
         1:begin
           results_seen=results_seen+1;
           if(checks!=expected_count(id) || dut.engine.total_checks!=checks)
             $fatal(1,"Wrong check count test=%h got=%d wanted=%d",id,checks,expected_count(id));
           if(dut.engine.error_checks!=(fault_for(id)?checks:0)) $fatal(1,"error_checks incorrect");
           if(dut.engine.q_errors!=((fault_for(id) && fault_mode!=2)?checks:0)) $fatal(1,"q_errors incorrect");
           if(dut.engine.qm_errors!=((fault_for(id) && fault_mode!=1)?checks:0)) $fatal(1,"qm_errors incorrect");
           if(dut.engine.passed!==!fault_for(id)) $fatal(1,"Incorrect result status");
           if(dut.engine.first_valid!== (fault_for(id)!=0)) $fatal(1,"Incorrect first-error flag");
         end
         2:begin
           errors_seen=errors_seen+1;
           if(!fault_for(id) || dut.engine.first_check!=1 || dut.engine.first_cycle!=first_cycle ||
              dut.engine.first_inputs!==first_inputs || dut.engine.first_actual!==first_actual ||
              dut.engine.first_expected!==first_expected || dut.engine.first_mask!==first_mask)
             $fatal(1,"First-error snapshot incorrect or overwritten");
         end
         3:complete_seen=complete_seen+1;
       endcase
     end
   end
 end
 initial begin
   wait(done);
   #100;
   if(running!==0 || failed!==(fault_mode!=0)) $fatal(1,"Final LED status incorrect");
   if(passed!==(fault_mode==0)) $fatal(1,"Suite status incorrect");
   if(starts_seen!=17 || results_seen!=17 || errors_seen!=(fault_mode==0?0:1) || complete_seen!=1)
     $fatal(1,"Missing or duplicate reports");
   if(lines!=35+(fault_mode==0?0:1) || characters!=0) $fatal(1,"Incomplete serial JSON stream");
   if(dut.engine.tests_done!=17 || dut.engine.failed_tests!=(fault_mode==0?0:1))
     $fatal(1,"Incorrect suite counters");
   $fclose(fd);
   $display("REGRESSION_PASS fault=%0d tests=%0d lines=%0d",fault_mode,results_seen,lines);
   $finish;
 end
 initial begin #20_000_000;$fatal(1,"Simulation timeout");end
endmodule
`default_nettype wire
