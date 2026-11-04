`default_nettype none
// Independent per-bit filters. Asserted input is normalized to logic1.
module swc_debounce #(parameter integer WIDTH=9, STABLE_CYCLES=1_000_000)(
 input wire clk,rst,input wire[WIDTH-1:0] async_pressed,
 output logic[WIDTH-1:0] pressed,press_pulse,release_pulse
);
 localparam integer CW=(STABLE_CYCLES<2)?1:$clog2(STABLE_CYCLES);
 wire[WIDTH-1:0] synced;
 swc_input_sync #(.WIDTH(WIDTH),.STAGES(2)) sync_inputs(.clk(clk),.rst(rst),.async_in(async_pressed),.sync_out(synced));
 logic[CW-1:0] count[0:WIDTH-1];
 always_ff @(posedge clk)begin
  press_pulse<='0;release_pulse<='0;
  if(rst)begin pressed<='0;for(integer i=0;i<WIDTH;i=i+1)count[i]<='0;end
  else for(integer i=0;i<WIDTH;i=i+1)begin
   if(synced[i]==pressed[i])count[i]<='0;
   else if(count[i]==CW'(STABLE_CYCLES-1))begin
    pressed[i]<=synced[i];count[i]<='0;
    press_pulse[i]<=synced[i];release_pulse[i]<=!synced[i];
   end else count[i]<=count[i]+1'b1;
  end
 end
 // synthesis translate_off
 initial if(STABLE_CYCLES<1)$fatal(1,"STABLE_CYCLES must be positive");
 // synthesis translate_on
endmodule
`default_nettype wire
