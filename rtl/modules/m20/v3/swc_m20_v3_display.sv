`default_nettype none
// FPGA State Visualizer. Reads snapshots only, has no CPU RAM write port.
module swc_m20_v3_display #(
 parameter integer FRAME_GAP_CYCLES=800000,RESET_CYCLES=500000,
 RELEASE_CYCLES=500000,ON_WAIT_CYCLES=5000000
)(input wire clk,rst,game,valid,input wire[1023:0] state_ram,
 input wire running,halted,trapped,
 output wire oled_rst_n,oled_dc,oled_cs_n,oled_sck,oled_mosi,
 output wire initialized,output logic[31:0] frames=0);
 import swc_oled_font_pkg::*;
 logic[1023:0] snapshot;logic snapshot_game,snapshot_valid,snapshot_running;
 logic snapshot_halted,snapshot_trapped;
 logic[31:0] gap=0;
 wire ready,done;wire start=ready&&gap==0&&!done;
 wire[9:0] address;wire request;logic pixel_valid=0;logic[7:0] pixels;
 function automatic[3:0] cell_value(input integer n);
  cell_value=snapshot[n*4+:4];
 endfunction
 function automatic[7:0] character(input integer n);
  reg[127:0] line;begin
   if(!snapshot_valid)line="M20 CPU BOOT    ";
   else if(snapshot_trapped)line="CPU TRAP        ";
   else if(snapshot_halted)line="CPU HALT        ";
   else if(snapshot_game&&cell_value(11)!=0)line="SNAKE B:RESTART ";
   else if(snapshot_game)line="M20 SNAKE S:00  ";
   else line="PONG L:00 R:00  ";
   character=line[(15-n)*8+:8];
   if(snapshot_valid)begin
    if(snapshot_game&&cell_value(11)==0)begin
     if(n==12)character=hex_char(cell_value(10));
     if(n==13)character=hex_char(cell_value(9));
    end else if(!snapshot_game)begin
     if(n==7)character=hex_char(cell_value(7));if(n==8)character=hex_char(cell_value(6));
     if(n==12)character=hex_char(cell_value(9));if(n==13)character=hex_char(cell_value(8));
    end
   end
  end
 endfunction
 function automatic[7:0] render(input[9:0] addr);
  integer x,y,p,cx,cy,local_y,head_slot,head_x,head_y,bitmap_address;
  reg[7:0] result;reg[127:0] boot_hint;reg occupied,food,head_pixel;begin
   x={25'b0,addr[6:0]};p={29'b0,addr[9:7]};result=0;
   boot_hint="KEY5: START     ";
   if(p==0)result=font_column(character(x/8),3'(x%8));
   else if(!snapshot_valid&&p==1)result=font_column(boot_hint[(15-x/8)*8+:8],3'(x%8));
   else if(snapshot_valid)for(integer b=0;b<8;b=b+1)begin
    y=p*8+b;cx=x/8;
    if(snapshot_game)begin
     cy=(y-8)/7;local_y=(y-8)%7;
     bitmap_address=192+cy*4+cx/4;
     occupied=(cell_value(bitmap_address)&(4'b1<<(cx%4)))!=0;
     food=cx==cell_value(7)&&cy==cell_value(8);
     head_slot=16*cell_value(1)+cell_value(0);
     head_x=cell_value(64+2*head_slot);head_y=cell_value(65+2*head_slot);
     head_pixel=cx==head_x&&cy==head_y;
     result[b]=(occupied&&x%8>=1&&x%8<=6&&local_y>=1&&local_y<=5)
        ||(food&&((x%8==3&&local_y>=1&&local_y<=5)||(local_y==3&&x%8>=1&&x%8<=5)));
     if(head_pixel&&local_y==2&&(x%8==2||x%8==5))result[b]=0;
    end else if(y<56)begin
     cy=(y-8)/6;local_y=(y-8)%6;
     result[b]=(cx==cell_value(0)&&cy==cell_value(1)&&x%8>=2&&x%8<=5&&local_y>=1&&local_y<=4)
       ||(x<3&&cy>=cell_value(4)&&cy<cell_value(4)+3)
       ||(x>=125&&cy>=cell_value(5)&&cy<cell_value(5)+3);
    end else if(y==63)result[b]=snapshot_running?(x%4==0):1'b1;
   end
   render=result;
  end
 endfunction
 always_ff @(posedge clk)begin
  pixel_valid<=request;
  if(request)pixels<=render(address);
  if(rst)begin gap<=0;frames<=0;snapshot<=0;snapshot_game<=0;snapshot_valid<=0;snapshot_running<=0;snapshot_halted<=0;snapshot_trapped<=0;pixel_valid<=0;pixels<=0;end
  else begin
   if(gap!=0)gap<=gap-1'b1;
   if(start)begin snapshot<=state_ram;snapshot_game<=game;snapshot_valid<=valid;snapshot_running<=running;snapshot_halted<=halted;snapshot_trapped<=trapped;end
   if(done)begin gap<=32'(FRAME_GAP_CYCLES);frames<=frames+1'b1;end
  end
 end
 swc_ssd1306 #(.SPI_HIGH_CYCLES(2),.SPI_LOW_CYCLES(3),.ROTATE_180(1),
  .RESET_CYCLES(RESET_CYCLES),.RELEASE_CYCLES(RELEASE_CYCLES),.ON_WAIT_CYCLES(ON_WAIT_CYCLES)) panel(
  .clk(clk),.rst(rst),.frame_start(start),.inverse(1'b0),.frame_ready(ready),.frame_done(done),.initialized(initialized),
  .pixel_addr(address),.pixel_req(request),.pixel_valid(pixel_valid),.pixel_data(pixels),
  .oled_rst_n(oled_rst_n),.oled_dc(oled_dc),.oled_cs_n(oled_cs_n),.oled_sck(oled_sck),.oled_mosi(oled_mosi));
endmodule
`default_nettype wire
