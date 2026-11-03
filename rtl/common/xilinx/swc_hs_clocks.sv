`default_nettype none
// Static configurations only. No live fabric clock mux or DRP operation.
module swc_hs_clocks #(
 parameter integer FREQUENCY_HZ=25_000_000,MULT=16,DIVIDE=32,
 parameter integer Q_PHASE=4,QM_PHASE=12
)(input wire sys_clk,rst,
 output wire base_clk,d_clk,q_clk,qm_clk,
 output wire base_ce,d_ce,q_ce,qm_ce,locked,clock_pin);
 generate if(FREQUENCY_HZ==1_000_000) begin:g_low
   reg [5:0] tick;
   reg pin_clock;
   localparam integer QT=(Q_PHASE*50+8)/16,MT=(QM_PHASE*50+8)/16;
   always @(posedge sys_clk) begin
     if(rst) begin tick<=0;pin_clock<=0;end
     else begin
       tick<=(tick==49)?0:tick+1'b1;
       pin_clock<=tick<25;
     end
   end
   assign base_clk=sys_clk;assign d_clk=sys_clk;
   assign q_clk=sys_clk;assign qm_clk=sys_clk;
   assign base_ce=!rst && tick==0;assign d_ce=!rst && tick==13;
   assign q_ce=!rst && tick==QT;assign qm_ce=!rst && tick==MT;
   assign clock_pin=pin_clock;assign locked=!rst;
 end else begin:g_mmcm
   wire fb,fb_buf,c0,c1,c2,c2b,c3,c3b,lock;
   // At divide >64 the MMCM counter cannot encode a full 360-degree delay.
   // Use the dedicated complementary output for the second half-cycle.
   // Selection is elaboration-time only: no fabric inverter or live clock mux.
   MMCME2_BASE #(.CLKIN1_PERIOD(20.0),.CLKFBOUT_MULT_F(1.0*MULT),
     .DIVCLK_DIVIDE(1),.CLKOUT0_DIVIDE_F(1.0*DIVIDE),
     .CLKOUT1_DIVIDE(DIVIDE),.CLKOUT1_PHASE(90.0),
     .CLKOUT2_DIVIDE(DIVIDE),.CLKOUT2_PHASE(22.5*(Q_PHASE%8)),
     .CLKOUT3_DIVIDE(DIVIDE),.CLKOUT3_PHASE(22.5*(QM_PHASE%8)),
     .BANDWIDTH("OPTIMIZED"),.STARTUP_WAIT("FALSE")) mmcm(
       .CLKIN1(sys_clk),.RST(rst),.PWRDWN(1'b0),.CLKFBIN(fb_buf),
       .CLKFBOUT(fb),.CLKFBOUTB(),.CLKOUT0(c0),.CLKOUT0B(),
       .CLKOUT1(c1),.CLKOUT1B(),.CLKOUT2(c2),.CLKOUT2B(c2b),
       .CLKOUT3(c3),.CLKOUT3B(c3b),.CLKOUT4(),.CLKOUT5(),.CLKOUT6(),.LOCKED(lock));
   BUFG feedback(.I(fb),.O(fb_buf));
   BUFG b0(.I(c0),.O(base_clk));BUFG b1(.I(c1),.O(d_clk));
   BUFG b2(.I(Q_PHASE>=8?c2b:c2),.O(q_clk));
   BUFG b3(.I(QM_PHASE>=8?c3b:c3),.O(qm_clk));
   ODDR #(.DDR_CLK_EDGE("SAME_EDGE"),.SRTYPE("ASYNC"),.INIT(1'b0)) forward_clock(
     .C(base_clk),.CE(1'b1),.D1(1'b1),.D2(1'b0),.R(rst || !lock),.S(1'b0),.Q(clock_pin));
   assign locked=lock;assign base_ce=1'b1;assign d_ce=1'b1;
   assign q_ce=1'b1;assign qm_ce=1'b1;
 end endgenerate
endmodule
`default_nettype wire
