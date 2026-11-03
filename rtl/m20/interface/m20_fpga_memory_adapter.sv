`default_nettype none
// FPGA peripheral only. Enables must come from the owner of the external CPU clock.
// Bus sampling assumes a separately verified stable window; no bitwise CDC fiction.
module m20_fpga_memory_adapter #(
 parameter string ROM_FILE=""
)(
 input wire sys_clk,rst,
 input wire rom_read_ce,ram_sample_ce,cpu_rise_ce,
 input wire [11:0] rom_addr,
 output logic [15:0] rom_data,
 input wire [7:0] ram_addr,
 input wire [3:0] ram_wdata,
 output logic [3:0] ram_rdata,
 input wire ram_ce,ram_oe,ram_we
);
 (* rom_style="block" *) logic [15:0] rom [0:4095];
 (* ram_style="block" *) logic [3:0] ram [0:255];
 logic pending_write;
 logic [7:0] pending_addr;
 logic [3:0] pending_data;
 initial if(ROM_FILE!="") $readmemh(ROM_FILE,rom);
 always_ff @(posedge sys_clk) begin
   if(rom_read_ce) rom_data<=rom[rom_addr]; // synchronous ROM output, held between service strobes
   if(rst) pending_write<=0;
   else begin
     if(cpu_rise_ce) begin
       if(pending_write) ram[pending_addr]<=pending_data;
       pending_write<=0;
     end
     if(ram_sample_ce) begin
       if(ram_ce && ram_oe && !ram_we) ram_rdata<=ram[ram_addr];
       pending_write<=ram_ce && ram_we && !ram_oe;
       pending_addr<=ram_addr;
       pending_data<=ram_wdata;
     end
   end
 end
endmodule
`default_nettype wire
