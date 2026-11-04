`default_nettype none
// Mode0/MSB first, one byte per CS transaction; all registers use clk.
module swc_spi_tx #(parameter integer HALF_CYCLES=25,
 HIGH_CYCLES=HALF_CYCLES,LOW_CYCLES=HALF_CYCLES)(
 input wire clk,rst,input wire[7:0] data,input wire valid,
 output wire ready,output logic done,output logic cs_n,sck,mosi
);
 localparam integer MAX_CYCLES=HIGH_CYCLES>LOW_CYCLES?HIGH_CYCLES:LOW_CYCLES;
 localparam integer CW=(MAX_CYCLES<2)?1:$clog2(MAX_CYCLES);
 localparam [2:0] IDLE=0,SETUP=1,HIGH=2,LOW=3,HOLD=4;
 logic[2:0] state;logic[CW-1:0] count;logic[2:0] bit_index;logic[7:0] saved;
 assign ready=state==IDLE;
 always_ff @(posedge clk)begin
  done<=0;
  if(rst)begin state<=IDLE;cs_n<=1;sck<=0;mosi<=0;count<=0;bit_index<=7;saved<=0;end
  else case(state)
   IDLE:if(valid)begin saved<=data;bit_index<=7;mosi<=data[7];cs_n<=0;count<=0;state<=SETUP;end
   SETUP:if(count==CW'(LOW_CYCLES-1))begin count<=0;sck<=1;state<=HIGH;end else count<=count+1'b1;
   HIGH:if(count==CW'(HIGH_CYCLES-1))begin
    count<=0;sck<=0;
    if(bit_index==0)state<=HOLD;
    else begin bit_index<=bit_index-1'b1;mosi<=saved[bit_index-1'b1];state<=LOW;end
   end else count<=count+1'b1;
   LOW:if(count==CW'(LOW_CYCLES-1))begin count<=0;sck<=1;state<=HIGH;end else count<=count+1'b1;
   HOLD:if(count==CW'(LOW_CYCLES-1))begin count<=0;cs_n<=1;state<=IDLE;done<=1;end else count<=count+1'b1;
   default:begin state<=IDLE;cs_n<=1;sck<=0;end
  endcase
 end
 // synthesis translate_off
 initial if(HIGH_CYCLES<1||LOW_CYCLES<1)$fatal(1,"SPI high/low periods must be positive");
 // synthesis translate_on
endmodule
`default_nettype wire
