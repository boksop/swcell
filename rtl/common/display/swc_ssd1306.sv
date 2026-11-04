`default_nettype none
// Write-only SSD1306 128x64 page-addressing driver. Data source uses req/valid.
module swc_ssd1306 #(
 parameter integer SPI_HALF_CYCLES=25,SPI_HIGH_CYCLES=SPI_HALF_CYCLES,
 SPI_LOW_CYCLES=SPI_HALF_CYCLES,RESET_CYCLES=500_000,
 RELEASE_CYCLES=500_000,ON_WAIT_CYCLES=5_000_000,
 parameter bit ROTATE_180=0
)(input wire clk,rst,input wire frame_start,inverse,
 output wire frame_ready,output logic frame_done,initialized,
 output wire[9:0] pixel_addr,output wire pixel_req,input wire pixel_valid,input wire[7:0] pixel_data,
 output logic oled_rst_n,oled_dc,output wire oled_cs_n,oled_sck,oled_mosi
);
 localparam [4:0] RESET_LOW=0,RELEASE_WAIT=1,INIT_PREP=2,INIT_ADV=3,PUSH=4,WAIT_BYTE=5,
 PAGE_PREP=6,PAGE_ADV=7,FETCH=8,DATA_ADV=9,ON_PREP=10,ON_WAIT=11,IDLE=12,INVERSE_PREP=13;
 logic[4:0] state,next_after_byte;logic[31:0] timer;
 logic[5:0] init_index;logic[1:0] page_command;logic[2:0] page;logic[6:0] column;
 logic clear_frame,applied_inverse;logic[7:0] tx_byte;wire spi_ready,spi_done;
 swc_spi_tx #(.HIGH_CYCLES(SPI_HIGH_CYCLES),.LOW_CYCLES(SPI_LOW_CYCLES)) spi(.clk(clk),.rst(rst),.data(tx_byte),.valid(state==PUSH),.ready(spi_ready),.done(spi_done),.cs_n(oled_cs_n),.sck(oled_sck),.mosi(oled_mosi));
 assign pixel_addr={page,column};assign pixel_req=state==FETCH&&!clear_frame;
 assign frame_ready=state==IDLE&&initialized;
 function automatic[7:0] init_byte(input[5:0] i);
  case(i)
   0:init_byte=8'hae;1:init_byte=8'hd5;2:init_byte=8'h80;
   3:init_byte=8'ha8;4:init_byte=8'h3f;5:init_byte=8'hd3;6:init_byte=0;
   7:init_byte=8'h40;8:init_byte=8'h8d;9:init_byte=8'h14;
   10:init_byte=8'h20;11:init_byte=8'h02;
   // Both axes are reversed relative to the original A1/C8 mounting orientation.
   12:init_byte=ROTATE_180?8'ha0:8'ha1;13:init_byte=ROTATE_180?8'hc0:8'hc8;
   14:init_byte=8'hda;15:init_byte=8'h12;16:init_byte=8'h81;17:init_byte=8'h7f;
   18:init_byte=8'hd9;19:init_byte=8'hf1;20:init_byte=8'hdb;21:init_byte=8'h40;
   22:init_byte=8'ha4;23:init_byte=8'ha6;24:init_byte=8'h2e;
   default:init_byte=8'he3;
  endcase
 endfunction
 always_ff @(posedge clk)begin
  frame_done<=0;
  if(rst)begin state<=RESET_LOW;next_after_byte<=IDLE;timer<=0;init_index<=0;page_command<=0;page<=0;column<=0;clear_frame<=1;applied_inverse<=0;tx_byte<=0;oled_rst_n<=0;oled_dc<=0;initialized<=0;end
  else case(state)
   RESET_LOW:if(timer==32'(RESET_CYCLES-1))begin timer<=0;oled_rst_n<=1;state<=RELEASE_WAIT;end else timer<=timer+1'b1;
   RELEASE_WAIT:if(timer==32'(RELEASE_CYCLES-1))begin timer<=0;state<=INIT_PREP;end else timer<=timer+1'b1;
   INIT_PREP:begin tx_byte<=init_byte(init_index);oled_dc<=0;next_after_byte<=INIT_ADV;state<=PUSH;end
   INIT_ADV:if(init_index==24)begin page<=0;column<=0;page_command<=0;state<=PAGE_PREP;end else begin init_index<=init_index+1'b1;state<=INIT_PREP;end
   PUSH:if(spi_ready)state<=WAIT_BYTE;
   WAIT_BYTE:if(spi_done)state<=next_after_byte;
   PAGE_PREP:begin
    oled_dc<=0;tx_byte<=page_command==0?(8'hb0|{5'b0,page}):(page_command==1?8'h00:8'h10);
    next_after_byte<=PAGE_ADV;state<=PUSH;
   end
   PAGE_ADV:if(page_command==2)begin page_command<=0;state<=FETCH;end else begin page_command<=page_command+1'b1;state<=PAGE_PREP;end
   FETCH:if(clear_frame||pixel_valid)begin tx_byte<=clear_frame?8'h00:pixel_data;oled_dc<=1;next_after_byte<=DATA_ADV;state<=PUSH;end
   DATA_ADV:if(column==127)begin
    column<=0;
    if(page==7)begin
     if(clear_frame)state<=ON_PREP;
     else begin frame_done<=1;state<=IDLE;end
    end else begin page<=page+1'b1;state<=PAGE_PREP;end
   end else begin column<=column+1'b1;state<=FETCH;end
   ON_PREP:begin tx_byte<=8'haf;oled_dc<=0;next_after_byte<=ON_WAIT;timer<=0;state<=PUSH;end
   ON_WAIT:if(timer==32'(ON_WAIT_CYCLES-1))begin timer<=0;clear_frame<=0;initialized<=1;state<=IDLE;end else timer<=timer+1'b1;
   IDLE:if(frame_start)begin page<=0;column<=0;page_command<=0;state<=INVERSE_PREP;end
   INVERSE_PREP:if(inverse!=applied_inverse)begin
    tx_byte<=inverse?8'ha7:8'ha6;applied_inverse<=inverse;
    oled_dc<=0;next_after_byte<=PAGE_PREP;state<=PUSH;
   end else state<=PAGE_PREP;
   default:begin state<=RESET_LOW;oled_rst_n<=0;initialized<=0;timer<=0;end
  endcase
 end
 // synthesis translate_off
 initial if(RESET_CYCLES<1||RELEASE_CYCLES<1||ON_WAIT_CYCLES<1)$fatal(1,"SSD1306 waits must be positive");
 // synthesis translate_on
endmodule
`default_nettype wire
