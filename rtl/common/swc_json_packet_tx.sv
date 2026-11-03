`default_nettype none
module swc_json_packet_tx #(parameter integer MAX_BYTES=2048)(
 input wire clk,rst,request,input wire [8*MAX_BYTES-1:0] packet,
 input wire [11:0] byte_count,output wire ready,
 output wire tx_valid,input wire tx_ready,output wire [7:0] tx_data
);
 reg active;reg [11:0] index,length;
 reg [8*MAX_BYTES-1:0] held;
 assign ready=!active;assign tx_valid=active;
 assign tx_data=held[(int'(length)-1-int'(index))*8+:8];
 always @(posedge clk) begin
   if(rst) begin active<=0;index<=0;length<=0;held<=0;end
   else if(!active) begin
     if(request) begin held<=packet;length<=byte_count;index<=0;active<=1;end
   end else if(tx_ready) begin
     if(index==length-1) active<=0;
     else index<=index+1'b1;
   end
 end
endmodule
`default_nettype wire
