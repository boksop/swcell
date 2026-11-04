`timescale 1ns/1ps
module m20_v24_fpga_memory #(
 parameter integer ROM_LATENCY=2,RAM_LATENCY=2
)(input wire sys_clk,rst,source_busy,source_fault,prime_rom,
 input wire [3:0]phase_state,
 input wire [11:0]rom_addr,output wire [15:0]rom_data,
 input wire [7:0]ram_addr,input wire [3:0]ram_wdata,output wire [3:0]ram_rdata,
 input wire ram_ce,ram_oe,ram_we);
 wire [15:0]rom_internal;wire [3:0]ram_internal;
 real rom_delay_ns=0,ram_delay_ns=0;
 wire pending_write=bram.pending_write;
 integer write_count=0,read_samples=0,sample_epoch=0,response_epoch=0;
 realtime last_response=-1e9;
 swc_v24_memory_service #(.ROM_LATENCY(ROM_LATENCY),.RAM_LATENCY(RAM_LATENCY)) bram(
 .service_clk(sys_clk),.rom_data(rom_internal),.ram_rdata(ram_internal),.*);
 assign #(rom_delay_ns)rom_data=rom_internal;
 assign #(ram_delay_ns)ram_rdata=ram_internal;
 always @(posedge sys_clk)if(!rst && !source_fault)begin
  if(bram.ram_count==1)begin response_epoch<=sample_epoch;last_response=$realtime;end
  if(bram.commit_write && pending_write)write_count<=write_count+1;
  if(bram.sample_ram && ram_ce && ram_oe && !ram_we)begin read_samples<=read_samples+1;sample_epoch<=sample_epoch+1;end
 end
endmodule
