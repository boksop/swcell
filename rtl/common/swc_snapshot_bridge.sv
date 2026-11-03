`default_nettype none
// Bundled-data handshake. Producer must hold payload and done until reset.
// done traverses 2 FFs, then 2 additional destination clocks precede capture.
module swc_snapshot_bridge #(parameter integer WIDTH=1)(
 input wire clk,rst,source_done,input wire [WIDTH-1:0] source_payload,
 output reg valid,output reg [WIDTH-1:0] payload
);
 (* ASYNC_REG="TRUE",SHREG_EXTRACT="NO" *) reg [1:0] done_sync;
 reg [1:0] settle;
 always @(posedge clk) begin
   if(rst) begin done_sync<=0;settle<=0;valid<=0;payload<=0;end
   else begin
     done_sync<={done_sync[0],source_done};
     if(done_sync[1] && !valid) begin
       if(settle==2) begin payload<=source_payload;valid<=1;end
       else settle<=settle+1'b1;
     end
   end
 end
endmodule
`default_nettype wire
