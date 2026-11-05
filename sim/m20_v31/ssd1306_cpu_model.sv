`timescale 1ns/1ps
// External receiver; no knowledge of CPU rendering variables or game RAM.
module ssd1306_cpu_model(input wire rst_n,cpu_reset,cs_n,dc,sck,mosi,
 output integer bytes=0,edges=0,output logic display_on=0);
 reg[7:0] ram[0:1023];reg[7:0] shift=0,pending=0;
 integer bits=0,page=0,column=0,clear_bytes=0;reg saved_dc;
 realtime selected=0,data_changed=0,last_rise=0,last_fall=0;
 always @(mosi)data_changed=$realtime;
 always @(negedge rst_n)begin display_on=0;pending=0;bits=0;end
 always @(negedge cs_n)if(rst_n)begin
  if(sck!==0)$fatal(1,"CPU_SPI_CPOL");
  bits=0;shift=0;saved_dc=dc;selected=$realtime;
 end
 always @(posedge sck)if(rst_n&&!cs_n)begin
  if(dc!==saved_dc)$fatal(1,"CPU_SPI_DC");
  if($realtime-selected<20||$realtime-data_changed<15)$fatal(1,"CPU_SPI_SETUP");
  if(last_rise!=0&&$realtime-last_rise<100)$fatal(1,"CPU_SPI_PERIOD");
  if(last_fall!=0&&$realtime-last_fall<20)$fatal(1,"CPU_SPI_LOW");
  shift={shift[6:0],mosi};bits=bits+1;edges=edges+1;last_rise=$realtime;
 end
 always @(negedge sck)if(rst_n&&!cs_n&&bits>0)begin
  if($realtime-last_rise<20)$fatal(1,"CPU_SPI_HIGH");last_fall=$realtime;
 end
 always @(posedge cs_n)if(rst_n&&bits!=0)begin
  if(cpu_reset)bits=0; // Explicit CPU reset may abort a partial serial byte.
  else begin
   if(bits!=8||sck!==0)$fatal(1,"CPU_SPI_BITCOUNT %d",bits);
   if($realtime-last_fall<10)$fatal(1,"CPU_SPI_HOLD");
   bytes=bytes+1;
   if(saved_dc)begin
    if(page>7||column>127)$fatal(1,"CPU_SPI_ADDRESS");
    ram[page*128+column]=shift;column=column+1;clear_bytes=clear_bytes+1;
   end else if(pending!=0)begin
    if(pending==8'h20&&shift!=2)$fatal(1,"CPU_SPI_PAGE_MODE");pending=0;
   end else if(shift>=8'hb0&&shift<=8'hb7)page=shift&7;
   else if(shift<16)column=(column&8'hf0)|(shift&15);
   else if(shift>=8'h10&&shift<=8'h1f)column=(column&15)|((shift&15)<<4);
   else case(shift)
    8'hae:begin display_on=0;clear_bytes=0;end
    8'haf:begin
     if(clear_bytes!=1024)$fatal(1,"CPU_SPI_CLEAR_LENGTH %d",clear_bytes);
     for(integer n=0;n<1024;n=n+1)if(ram[n]!==0)$fatal(1,"CPU_SPI_CLEAR_CONTENT");
     display_on=1;
    end
    8'hd5,8'ha8,8'hd3,8'h8d,8'h20,8'hda,8'h81,8'hd9,8'hdb:pending=shift;
    8'h40,8'ha0,8'hc0,8'ha4,8'ha6,8'h2e:begin end
    default:$fatal(1,"CPU_SPI_COMMAND %h",shift);
   endcase
   bits=0;
  end
 end
endmodule
