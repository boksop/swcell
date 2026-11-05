`default_nettype none
// Six continuous input levels. Synchronization is NOT debouncing.
module swc_m20_v31_gpio(
 input wire clk,power_reset,KEY0,KEY1,KEY2,KEY3,KEY5,KEY6,
 input wire[3:0] gpo,output wire[5:0] keys,
 output wire oled_cs_n,oled_dc,oled_sck,oled_mosi);
 swc_input_sync #(.WIDTH(6),.STAGES(2)) sync_keys(
  .clk(clk),.rst(power_reset),.async_in(~{KEY6,KEY5,KEY1,KEY3,KEY0,KEY2}),.sync_out(keys));
 assign {oled_cs_n,oled_dc,oled_sck,oled_mosi}=gpo;
endmodule
`default_nettype wire
