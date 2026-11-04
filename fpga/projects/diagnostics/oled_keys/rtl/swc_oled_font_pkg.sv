`default_nettype none
package swc_oled_font_pkg;
 function automatic[7:0] hex_char(input[3:0] value);
  hex_char=value<10?(8'h30+{4'b0,value}):(8'h41+{4'b0,value}-8'd10);
 endfunction
 function automatic[7:0] font_column(input[7:0] character,input[2:0] column);
  reg[39:0] bits;begin
   case(character)
    8'h20:bits=40'h0000000000;
    8'h30:bits=40'h3E5149453E;
    8'h31:bits=40'h00427F4000;
    8'h32:bits=40'h4261514946;
    8'h33:bits=40'h2141454B31;
    8'h34:bits=40'h1814127F10;
    8'h35:bits=40'h2745454539;
    8'h36:bits=40'h3C4A494930;
    8'h37:bits=40'h0101710907;
    8'h38:bits=40'h3649494936;
    8'h39:bits=40'h064949291E;
    8'h41:bits=40'h7E1111117E;
    8'h42:bits=40'h7F49494936;
    8'h43:bits=40'h3E41414122;
    8'h44:bits=40'h7F4141221C;
    8'h45:bits=40'h7F49494941;
    8'h46:bits=40'h7F09090901;
    8'h47:bits=40'h3E41495132;
    8'h48:bits=40'h7F0808087F;
    8'h49:bits=40'h00417F4100;
    8'h4a:bits=40'h2040413F01;
    8'h4b:bits=40'h7F08142241;
    8'h4c:bits=40'h7F40404040;
    8'h4d:bits=40'h7F020C027F;
    8'h4e:bits=40'h7F0408107F;
    8'h4f:bits=40'h3E4141413E;
    8'h50:bits=40'h7F09090906;
    8'h51:bits=40'h3E4151215E;
    8'h52:bits=40'h7F09192946;
    8'h53:bits=40'h4649494931;
    8'h54:bits=40'h01017F0101;
    8'h55:bits=40'h3F4040403F;
    8'h56:bits=40'h1F2040201F;
    8'h57:bits=40'h3F4038403F;
    8'h58:bits=40'h6314081463;
    8'h59:bits=40'h0708700807;
    8'h5a:bits=40'h6151494543;
    8'h3a:bits=40'h0036360000;
    8'h3d:bits=40'h1414141414;
    8'h2d:bits=40'h0808080808;
    8'h2f:bits=40'h2010080402;
    8'h3f:bits=40'h0201510906;
    default:bits=40'h0201510906;
   endcase
   font_column=column<5?bits[(4-column)*8+:8]:8'h00;
  end
 endfunction
endpackage
`default_nettype wire
