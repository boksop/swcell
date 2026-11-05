`timescale 1ns/1ps
module tb_m20_v31_joint #(parameter ROM_FILE="");
 logic sys_clk=0;always #10 sys_clk=~sys_clk;
 logic RST_N=1,KEY0=1,KEY1=1,KEY2=1,KEY3=1,KEY4=1,KEY5=1,KEY6=1,KEY7=1,UART_RXD=1;
 wire OLED_RST_N,OLED_DC,OLED_SCK,OLED_MOSI,OLED_CS_N,UART_TX;
 wire LED0,LED1,LED2,LED3,LED4,LED5,LED6,LED7;
 swcell_m20_v31_top #(.ROM_FILE(ROM_FILE),.POR_CYCLES(5),.OLED_RESET_CYCLES(200),
  .OLED_RELEASE_CYCLES(100),.DEBUG_DEBOUNCE_CYCLES(4),.REPORT_CYCLES(500000)) dut(.*);
 wire cpu_reset=dut.service.cpu_reset;
 wire commit_ce=dut.service.commit_ce;
 wire[3:0] gpo=dut.service.gpo;
 wire[11:0] pc=dut.service.pc;
 integer spi_bytes,spi_edges;wire display_on;
 ssd1306_cpu_model panel(.rst_n(OLED_RST_N),.cpu_reset(cpu_reset),.cs_n(OLED_CS_N),.dc(OLED_DC),
  .sck(OLED_SCK),.mosi(OLED_MOSI),.bytes(spi_bytes),.edges(spi_edges),.display_on(display_on));
 // Independent V1 core advances at exactly the same logical commit boundary.
 logic reference_clk=0;
 always @(posedge sys_clk)if(commit_ce)reference_clk=1;
 always @(negedge sys_clk)reference_clk=0;
 wire[11:0] r_pc,r_rom;wire[7:0] r_ar,r_addr;wire[3:0] r_a,r_gpo,r_data;
 wire r_z,r_c,r_ce,r_oe,r_we,r_retire;wire[2:0] r_state;
 m20_cpu_core reference(.clk(reference_clk),.rst(cpu_reset),.keys(dut.service.held_keys),
  .rom_data(dut.service.instruction),.ram_rdata(dut.service.ram_rdata),.rom_addr(r_rom),
  .ram_addr(r_addr),.ram_wdata(r_data),.ram_ce(r_ce),.ram_oe(r_oe),.ram_we(r_we),
  .dbg_pc(r_pc),.dbg_ar(r_ar),.dbg_a(r_a),.dbg_z(r_z),.dbg_c(r_c),.dbg_gpo(r_gpo),.dbg_state(r_state),
  .retire_valid(r_retire));
 integer vectors,rc,checked=0,write_count=0,uart_bytes=0,raw,out_trace;string outdir=".";
 logic[63:0] expected;logic[3:0] last_gpo=8;
 reg[3:0] final_ram[0:255];
 task next_vector;
  rc=$fscanf(vectors,"%h\n",expected);
  if(rc==1)begin
   {KEY6,KEY5,KEY1,KEY3,KEY0,KEY2}=~expected[5:0];
  end
 endtask
 initial begin
  if(!$value$plusargs("OUT=%s",outdir))$fatal(1,"OUT required");
  vectors=$fopen({outdir,"/vectors.hex"},"r");if(!vectors)$fatal(1,"no vectors");
  $readmemh({outdir,"/final_ram.memh"},final_ram);
  raw=$fopen({outdir,"/uart.jsonl"},"wb");
  out_trace=$fopen({outdir,"/cpu_out.csv"},"w");$fwrite(out_trace,"micro,retired,pc,gpo\n");
  next_vector();
 end
 always @(posedge sys_clk)begin
  if(dut.service.write_commit)write_count=write_count+1;
  if(commit_ce)begin
   if(!cpu_reset)begin
    if({r_addr,r_data,r_ce,r_oe,r_we,r_retire}!=={dut.service.ram_addr,dut.service.ram_wdata,
       dut.service.ram_ce,dut.service.ram_oe,dut.service.ram_we,dut.service.retire_valid})$fatal(1,"V31_V1_BUS");
   end
   #1;
   if(!cpu_reset)begin
    if({r_pc,r_ar,r_a,r_z,r_c,r_gpo,r_state}!=={pc,dut.service.ar,dut.service.accumulator,
       dut.service.z,dut.service.c,gpo,dut.service.ustate})$fatal(1,"V31_V1_STATE");
    if(dut.service.held_retire&&dut.service.held_word==16'he200)$fwrite(out_trace,"%0d,%0d,%03h,%01h\n",dut.service.microcycles,dut.service.retired,dut.service.held_pc,gpo);
    if(last_gpo!==gpo&&dut.service.held_word!=16'he200)$fatal(1,"V31_GPO_NOT_OUT");
    if(dut.service.held_retire)begin
     if(expected[63:6]!=={dut.service.held_pc,dut.service.held_word,pc,dut.service.ar,
        dut.service.accumulator,dut.service.z,dut.service.c,gpo})
       $fatal(1,"V31_PYTHON_STATE index=%d pc=%h expected=%h",checked,pc,expected);
     checked=checked+1;
     if(checked%100000==0)$display("V31_PROGRESS checked=%d bytes=%d",checked,spi_bytes);
     @(negedge sys_clk);next_vector();
     if(rc!=1)begin
      for(integer n=0;n<256;n=n+1)if(dut.service.memory.memory[n]!==final_ram[n])$fatal(1,"V31_FINAL_RAM %d",n);
      if(dut.service.errors!=0||!display_on||spi_edges!=8*spi_bytes)$fatal(1,"V31_FINAL_PROTOCOL");
      $fflush(raw);$fclose(out_trace);
      $display("M20_V31_JOINT_PASS checked=%d bytes=%d writes=%d",checked,spi_bytes,write_count);$finish;
     end
    end
   end
   last_gpo=gpo;
  end
  if(dut.keys!==dut.gpio.keys)$fatal(1,"V31_KEYS_BYPASS");
  if(!cpu_reset&&{OLED_CS_N,OLED_DC,OLED_SCK,OLED_MOSI}!==gpo)$fatal(1,"V31_GPIO_BYPASS");
 end
 reg[7:0] uart_value;
 always begin
  @(negedge UART_TX);#4340;if(UART_TX!==0)$fatal(1,"V31_UART_START");
  for(integer b=0;b<8;b=b+1)begin #8680;uart_value[b]=UART_TX;end
  #8680;if(UART_TX!==1)$fatal(1,"V31_UART_STOP");
  $fwrite(raw,"%c",uart_value);$fflush(raw);uart_bytes=uart_bytes+1;
 end
 always @(posedge OLED_RST_N)if(dut.gpo!==4'h8||dut.service.active)$fatal(1,"V31_GPIO_NOT_READY_BEFORE_OLED_RELEASE");
 // Debug test: stop during normal execution, one microstep, resume.
 logic[63:0] saved_micro,saved_writes;logic[32:0] saved_state;
 initial begin
  wait(checked==1000);
  @(negedge sys_clk);KEY7=0;repeat(12)@(negedge sys_clk);KEY7=1;
  wait(!dut.service.active&&!dut.service.run_requested);repeat(10)@(negedge sys_clk);
  saved_micro=dut.service.microcycles;saved_writes=dut.service.writes;
  saved_state={pc,dut.service.ar,dut.service.accumulator,dut.service.z,dut.service.c,gpo,dut.service.ustate};
  repeat(300)@(negedge sys_clk);
  if(saved_micro!=dut.service.microcycles||saved_writes!=dut.service.writes||
   saved_state!=={pc,dut.service.ar,dut.service.accumulator,dut.service.z,dut.service.c,gpo,dut.service.ustate})$fatal(1,"V31_STOP");
  // Send UART n, 115200 8N1, through the real pin/receiver.
  send_uart(8'h6e);wait(dut.service.microcycles==saved_micro+1);wait(!dut.service.active);
  repeat(100)@(negedge sys_clk);
  if(dut.service.microcycles!=saved_micro+1)$fatal(1,"V31_STEP");
  send_uart(8'h20);
 end
 task send_uart(input[7:0] value);
  UART_RXD=0;repeat(434)@(negedge sys_clk);
  for(integer b=0;b<8;b=b+1)begin UART_RXD=value[b];repeat(434)@(negedge sys_clk);end
  UART_RXD=1;repeat(434)@(negedge sys_clk);
 endtask
 initial begin #(64'd20000000000);$fatal(1,"V31_TIMEOUT checked=%d",checked);end
endmodule
