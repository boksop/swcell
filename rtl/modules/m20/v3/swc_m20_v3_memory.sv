`default_nettype none
// Two immutable program banks, one 4096-word CPU address space. No instruction decode.
module swc_m20_v3_memory #(
 parameter PONG_FILE="",SNAKE_FILE=""
)(input wire clk,cancel,game,rom_req,ram_req,write_ce,
 input wire[11:0] rom_addr,output logic[15:0] rom_data,
 input wire[7:0] ram_addr,input wire[3:0] ram_wdata,
 input wire ram_ce,ram_oe,ram_we,output logic[3:0] ram_data,
 input wire[7:0] view_addr,output logic[3:0] view_data,
 output wire write_commit,read_commit);
 (* ram_style="block" *)logic[15:0] pong[0:4095],snake[0:4095];
 (* ram_style="block" *)logic[3:0] memory[0:255];
 logic[11:0] rom_held;logic rom_game,rom_pending=0;
 logic[7:0] read_held,write_addr;logic[3:0] write_data;
 logic read_pending=0,write_pending=0;
 initial begin
  for(integer i=0;i<4096;i=i+1)begin pong[i]=16'hffff;snake[i]=16'hffff;end
  if(PONG_FILE!="")$readmemh(PONG_FILE,pong);
  if(SNAKE_FILE!="")$readmemh(SNAKE_FILE,snake);
  for(integer i=0;i<256;i=i+1)memory[i]=0;
 end
 assign write_commit=write_ce&&write_pending&&!cancel;
 assign read_commit=read_pending&&!cancel;
 always_ff @(posedge clk)begin
  rom_pending<=rom_req;
  if(rom_req)begin rom_held<=rom_addr;rom_game<=game;end
  if(rom_pending)rom_data<=rom_game?snake[rom_held]:pong[rom_held];
  // The second port is read-only. It cannot advance the game.
  view_data<=memory[view_addr];
  read_pending<=0;
  if(cancel)begin write_pending<=0;read_pending<=0;end
  else begin
   if(read_pending)ram_data<=memory[read_held];
   if(write_ce)begin
    if(write_pending)memory[write_addr]<=write_data;
    write_pending<=0;
   end
   if(ram_req)begin
    read_pending<=ram_ce&&ram_oe&&!ram_we;
    read_held<=ram_addr;
    write_pending<=ram_ce&&ram_we&&!ram_oe;
    write_addr<=ram_addr;write_data<=ram_wdata;
   end
  end
 end
endmodule
`default_nettype wire
