`timescale 1ns/1ps
// Independent receiver/parser. GDDRAM is deliberately NOT initialized by RESET.
module ssd1306_spi_model(input wire rst_n,cs_n,dc,sck,mosi,
 output reg display_on=0,inverse=0,output integer data_bytes=0,command_bytes=0,transactions=0);
 reg[7:0] ram[0:1023];reg[7:0] shift;integer bits=0,page=0,column=0;
 reg saved_dc;reg[7:0] pending=0;reg page_mode=0,pump=0;reg[7:0] mux_ratio=0,com_config=0;
 real reset_time=0,select_time=0,last_data=0,last_clock=0,last_rise=0,last_fall=0;
 reg saw_clock=0;
 reg seg_remap,com_reverse;integer inverse_commands=0;
 always @(negedge rst_n)begin reset_time=$realtime;display_on=0;pending=0;page_mode=0;pump=0;bits=0;end
 always @(posedge rst_n)if($realtime>0&&$realtime-reset_time<3000.0)$fatal(1,"MODEL_RESET_SHORT");
 always @(negedge cs_n)begin
  if(!rst_n)$fatal(1,"MODEL_SELECTED_IN_RESET");
  if(sck!==0)$fatal(1,"MODEL_SPI_CPOL");
  select_time=$realtime;bits=0;shift=0;saved_dc=dc;
 end
 always @(dc)if(!cs_n&&rst_n)$fatal(1,"MODEL_DC_CHANGED_SELECTED");
 always @(mosi)last_data=$realtime;
 always @(posedge sck)if(rst_n&&!cs_n)begin
  if(dc!==saved_dc)$fatal(1,"MODEL_DC_UNSTABLE");
  if($realtime-select_time<20.0||$realtime-last_data<15.0)$fatal(1,"MODEL_SPI_SETUP");
  if(saw_clock&&$realtime-last_clock<20.0)$fatal(1,"MODEL_SPI_LOW_SHORT");
  if(last_rise>0&&$realtime-last_rise<100.0)$fatal(1,"MODEL_SPI_PERIOD_SHORT");
  last_rise=$realtime;last_clock=$realtime;saw_clock=1;
  shift={shift[6:0],mosi};bits=bits+1;
  if(bits>8)$fatal(1,"MODEL_EXTRA_SPI_CLOCK");
 end
 always @(negedge sck)if(rst_n&&!cs_n&&bits>0)begin
  if($realtime-last_clock<20.0)$fatal(1,"MODEL_SPI_HIGH_SHORT");
  last_clock=$realtime;last_fall=$realtime;
 end
 always @(posedge cs_n)if(rst_n&&bits>0)begin
  if(bits!=8||sck!==0)$fatal(1,"MODEL_INCOMPLETE_TRANSACTION");
  if($realtime-last_fall<10.0)$fatal(1,"MODEL_SPI_HOLD");
  transactions=transactions+1;
  if(saved_dc)begin
   if(!page_mode||column>127||page>7)$fatal(1,"MODEL_ADDRESS_MODE");
   ram[page*128+column]=shift;column=column+1;data_bytes=data_bytes+1;
  end else begin
   command_bytes=command_bytes+1;
   if(pending!=0)begin
    case(pending)
     8'h20:begin if(shift!=2)$fatal(1,"MODEL_EXPECTS_PAGE_MODE");page_mode=1;end
     8'h8d:pump=(shift==8'h14);
     8'ha8:mux_ratio=shift;
     8'hda:com_config=shift;
     default:begin end
    endcase
    pending=0;
   end else if(shift>=8'hb0&&shift<=8'hb7)page=shift&7;
   else if(shift<=8'h0f)column=(column&8'hf0)|(shift&15);
   else if(shift>=8'h10&&shift<=8'h1f)column=(column&15)|((shift&15)<<4);
   else case(shift)
    8'hae:display_on=0;
    8'haf:begin
     if(!pump||mux_ratio!=63||com_config!=8'h12||data_bytes!=1024)$fatal(1,"MODEL_INVALID_INIT_OR_CLEAR");
     for(integer n=0;n<1024;n=n+1)if(ram[n]!==0)$fatal(1,"MODEL_GDDRAM_NOT_CLEARED");
     display_on=1;
    end
    8'ha6:begin inverse=0;inverse_commands=inverse_commands+1;end
    8'ha7:begin inverse=1;inverse_commands=inverse_commands+1;end
    8'ha0:seg_remap=0;
    8'ha1:seg_remap=1;
    8'hc0:com_reverse=0;
    8'hc8:com_reverse=1;
    8'hd5,8'ha8,8'hd3,8'h8d,8'h20,8'hda,8'h81,8'hd9,8'hdb:pending=shift;
    8'h40,8'ha4,8'h2e,8'he3:begin end
    default:$fatal(1,"MODEL_UNKNOWN_COMMAND %h",shift);
   endcase
  end
  bits=0;
 end
endmodule
