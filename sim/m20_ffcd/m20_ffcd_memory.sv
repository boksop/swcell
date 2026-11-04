`timescale 1ns/1ps
module m20_ffcd_memory #(
 parameter integer ROM_LATENCY=2,RAM_LATENCY=2
)(input wire sys_clk,rst,rom_read_ce,ram_sample_ce,commit_ce,write_ce,prime_rom,
 input wire [11:0] rom_addr,output wire [15:0] rom_data,
 input wire [7:0] ram_addr,input wire [3:0] ram_wdata,output wire [3:0] ram_rdata,
 input wire ram_ce,ram_oe,ram_we);
 wire [15:0] rom_internal;wire [3:0]ram_internal;
 real rom_delay_ns=0,ram_delay_ns=0;
 wire pending_write=bram.pending_write;
 integer write_count=0,read_samples=0,sample_epoch=0,response_epoch=0;
 realtime last_response=-1e9;
 swc_fpga_memory_adapter #(.ROM_LATENCY(ROM_LATENCY),.RAM_LATENCY(RAM_LATENCY))bram(
 .sys_clk(sys_clk),.rst(rst),.rom_read_ce(rom_read_ce),.ram_sample_ce(ram_sample_ce),.commit_ce(write_ce),.prime_rom(prime_rom),
 .rom_addr(rom_addr),.rom_data(rom_internal),.ram_addr(ram_addr),.ram_wdata(ram_wdata),.ram_rdata(ram_internal),.ram_ce(ram_ce),.ram_oe(ram_oe),.ram_we(ram_we));
 assign #(rom_delay_ns)rom_data=rom_internal;
 assign #(ram_delay_ns)ram_rdata=ram_internal;
 always @(posedge sys_clk)if(!rst)begin
  if(bram.ram_count==1)begin response_epoch<=sample_epoch;last_response=$realtime;end
  if(write_ce&&pending_write)write_count<=write_count+1;
  if(ram_sample_ce&&ram_ce&&ram_oe&&!ram_we)begin read_samples<=read_samples+1;sample_epoch<=sample_epoch+1;end
 end
endmodule
