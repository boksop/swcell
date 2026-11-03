`timescale 1ns/1ps
module tb_m20_fpga_adapter;
 reg sys_clk=0,rst=1,cpu_clk=0;
 always #10 sys_clk=~sys_clk;
 integer phase=0,cycles=0,retired=0,writes=0,i;
 wire rom_read_ce=(phase==10),ram_sample_ce=(phase==35),cpu_rise_ce=(phase==0);
 always @(posedge sys_clk)begin
  phase<=phase==49?0:phase+1;
  if(phase==0)cpu_clk<=1;
  if(phase==25)cpu_clk<=0;
  if(!rst && cpu_rise_ce && peripheral.pending_write)writes=writes+1;
 end
 wire [11:0] rom_addr;wire [15:0] rom_data;wire [7:0] ram_addr;wire [3:0] ram_rdata,ram_wdata;
 wire ram_ce,ram_oe,ram_we;wire [3:0] dbg_a,dbg_gpo;wire halted,trapped,retire_valid;
 m20v21_cpu_core cpu(.clk(cpu_clk),.rst(rst),.keys(6'd0),.rom_addr(rom_addr),.rom_data(rom_data),
  .ram_addr(ram_addr),.ram_rdata(ram_rdata),.ram_wdata(ram_wdata),.ram_ce(ram_ce),.ram_oe(ram_oe),.ram_we(ram_we),
  .dbg_a(dbg_a),.dbg_gpo(dbg_gpo),.halted(halted),.trapped(trapped),.retire_valid(retire_valid));
 m20_fpga_memory_adapter peripheral(.*);
 always @(posedge cpu_clk)if(!rst)begin cycles=cycles+1;if(retire_valid)retired=retired+1;end
 initial begin
  for(i=0;i<4096;i=i+1)peripheral.rom[i]=16'hffff;
  for(i=0;i<256;i=i+1)peripheral.ram[i]=4'ha;
  peripheral.rom[0]=16'h0005;peripheral.rom[1]=16'h8122;peripheral.rom[2]=16'h8022;
  peripheral.rom[3]=16'hE200;peripheral.rom[4]=16'hF100;
  repeat(3)@(negedge cpu_clk);rst=0;
  wait(halted);#10;
  if(trapped || dbg_a!==5 || dbg_gpo!==5 || peripheral.ram[8'h22]!==5 || retired!=5 || writes!=1 || cycles!=17)
   $fatal(1,"adapter integration mismatch a=%h out=%h cycles=%d retired=%d writes=%d",dbg_a,dbg_gpo,cycles,retired,writes);
  // A raw bus glitch outside the qualified sampling window must never clock a write.
  wait(phase==5);#1;
  force ram_ce=1;force ram_we=1;force ram_oe=0;force ram_addr=8'h23;force ram_wdata=4'h9;
  #5;release ram_ce;release ram_we;release ram_oe;release ram_addr;release ram_wdata;
  repeat(50)@(posedge sys_clk);#1;
  if(peripheral.ram[8'h23]!==4'ha || writes!=1)$fatal(1,"unqualified WE glitch caused write");
  // Pending write is cancelled even after sampling if reset precedes the next effective CPU edge.
  @(negedge sys_clk);peripheral.pending_write=1;peripheral.pending_addr=8'h23;peripheral.pending_data=9;rst=1;
  repeat(60)@(posedge sys_clk);#1;
  if(peripheral.ram[8'h23]!==4'ha)$fatal(1,"pending reset write not cancelled");
  $display("M20_FPGA_ADAPTER_PASS rom_sync=1 ram_sync=1 retired=5 cycles=17 writes=1 reset_abort=1 glitch_filter=1");$finish;
 end
 initial begin #100000;$fatal(1,"adapter watchdog");end
endmodule
