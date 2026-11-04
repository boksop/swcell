`timescale 1ns/1ps
// service_clk is the opposite edge of the SAME CLK_REF; no private Johnson counter.
module swc_v24_memory_service #(
 parameter integer ROM_LATENCY=2,RAM_LATENCY=2,
 parameter ROM_INIT_FILE=""
)(input wire service_clk,rst,source_busy,source_fault,prime_rom,
 input wire [3:0] phase_state,
 input wire [11:0] rom_addr,output logic [15:0] rom_data,
 input wire [7:0] ram_addr,input wire [3:0] ram_wdata,output logic [3:0] ram_rdata,
 input wire ram_ce,ram_oe,ram_we);
 (* ram_style="block" *)logic [15:0]rom[0:4095];
 (* ram_style="block" *)logic [3:0]memory[0:255];
 logic [11:0]held_rom_addr;logic [7:0]held_ram_addr,pending_addr;
 logic [3:0]pending_data;logic pending_write=0;
 integer rom_count=0,ram_count=0;
 wire serve=source_busy && !source_fault;
 wire sample_ram=serve && phase_state==4'b0000;
 wire sample_rom=serve && phase_state==4'b1111;
 wire commit_write=serve && phase_state==4'b0111;
 initial begin
  if(ROM_INIT_FILE!="")$readmemh(ROM_INIT_FILE,rom);
  if(ROM_LATENCY<1 || RAM_LATENCY<1)$fatal(1,"V24_BAD_BRAM_LATENCY");
 end
 always @(posedge service_clk)begin
  if(prime_rom || (!rst && sample_rom))begin held_rom_addr<=rom_addr;rom_count<=ROM_LATENCY;end
  else if(rom_count>0)begin rom_count<=rom_count-1;if(rom_count==1)rom_data<=rom[held_rom_addr];end
  if(rst || source_fault)begin pending_write<=0;ram_count<=0;end
  else begin
   if(ram_count>0)begin ram_count<=ram_count-1;if(ram_count==1)ram_rdata<=memory[held_ram_addr];end
   if(commit_write)begin
    if(pending_write)memory[pending_addr]<=pending_data;
    pending_write<=0;
   end
   if(sample_ram)begin
    pending_write<=ram_ce && ram_we && !ram_oe;pending_addr<=ram_addr;pending_data<=ram_wdata;
    if(ram_ce && ram_oe && !ram_we)begin held_ram_addr<=ram_addr;ram_count<=RAM_LATENCY;end
   end
  end
 end
endmodule
