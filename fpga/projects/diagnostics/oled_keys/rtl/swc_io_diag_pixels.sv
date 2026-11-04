`default_nettype none
module swc_io_diag_pixels(
 input wire[9:0] address,input wire[3:0] mode,input wire[8:0] keys,seen,
 input wire[3:0] last_key,input wire last_down,input wire[31:0] events,seconds,frames,
 output logic[7:0] data
);
 import swc_oled_font_pkg::*;
 wire[2:0] page=address[9:7];wire[6:0] x=address[6:0];wire[3:0] char_index=address[6:3];
 reg[127:0] text_line;reg[7:0] character;integer key_index;
 always_comb begin
  text_line="                ";character=" ";key_index=0;
  case(page)
   0:text_line="SWCELL IO TEST  ";
   1:text_line="RST:0 KEYS:00   ";
   2:text_line="LAST: NONE      ";
   3:text_line="K0=0 K1=0 K2=0  ";
   4:text_line="K3=0 K4=0 K5=0  ";
   5:text_line="K6=0 K7=0 R=0   ";
   6:text_line="SEEN:000 EV:0000";
   7:text_line="UP:0000 MODE:0  ";
  endcase
  character=text_line[(15-char_index)*8+:8];
  if(page==1)begin
   if(char_index==4)character=keys[8]?"1":"0";
   if(char_index==11)character=hex_char(keys[7:4]);
   if(char_index==12)character=hex_char(keys[3:0]);
  end
  if(page==2&&last_key<9)begin
   if(char_index==6)character=last_key==8?"R":"K";
   if(char_index==7)character=last_key==8?"S":"E";
   if(char_index==8)character=last_key==8?"T":"Y";
   if(char_index==9)character=last_key==8?" ":hex_char(last_key);
   if(char_index>=11&&char_index<=14)begin
    if(last_down)case(char_index)11:character="D";12:character="O";13:character="W";14:character="N";endcase
    else case(char_index)11:character="U";12:character="P";default:character=" ";endcase
   end
  end
  if(page==3||page==4)begin
   if(char_index==3||char_index==8||char_index==13)begin
    key_index=(page==3?0:3)+(char_index==3?0:char_index==8?1:2);
    character=keys[key_index]?"1":"0";
   end
  end
  if(page==5)begin
   if(char_index==3)character=keys[6]?"1":"0";
   if(char_index==8)character=keys[7]?"1":"0";
   if(char_index==12)character=keys[8]?"1":"0";
  end
  if(page==6)begin
   if(char_index==5)character=hex_char({3'b0,seen[8]});
   if(char_index==6)character=hex_char(seen[7:4]);
   if(char_index==7)character=hex_char(seen[3:0]);
   if(char_index>=12)character=hex_char(events[(15-char_index)*4+:4]);
  end
  if(page==7)begin
   if(char_index>=3&&char_index<=6)character=hex_char(seconds[(6-char_index)*4+:4]);
   if(char_index==13)character=hex_char(mode);
  end
  data=font_column(character,x[2:0]);
  case(mode)
   0:data=0;
   1:data=8'hff;
   2:data=(x[3]^page[0])?8'hff:8'h00;
   3:data=x[0]?8'haa:8'h55;
   4:data=x[2]?8'hff:8'h00;
   5:data=8'h0f;
   6:begin
    data=0;
    for(integer bitn=0;bitn<8;bitn=bitn+1)
     data[bitn]=(x==0||x==127||({page,3'b000}+bitn)==0||({page,3'b000}+bitn)==63||x==2*({page,3'b000}+bitn)||x==127-2*({page,3'b000}+bitn));
   end
   7:begin
    data=0;
    for(integer bitn=0;bitn<8;bitn=bitn+1)data[bitn]=(x==frames[6:0]||({page,3'b000}+bitn)==frames[5:0]);
   end
   default:begin end
  endcase
 end
endmodule
`default_nettype wire
