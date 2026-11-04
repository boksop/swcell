`timescale 1ns/1ps
module tb_ff16_structure;
 logic c=0,p=1;wire [3:0]h,s,cd,t4,t8,t12,t16,hr,sr;
 logic a=0,b=0,sel=0;wire y;
 integer i,n,vectors=0;
 swc_ff16_mux157 primitive_dut(.s(sel),.i0(a),.i1(b),.y(y));
 swc_ff16_phasegen #(.TAP_STAGES(4))u4(.clk_ref(c),.safe_hold(p),.master_hold(h[0]),.slave_open(s[0]),.delayed_ref(cd[0]),.tap4(t4[0]),.tap8(t8[0]),.tap12(t12[0]),.tap16(t16[0]),.h_raw(hr[0]),.s_raw(sr[0]));
 swc_ff16_phasegen #(.TAP_STAGES(8))u8(.clk_ref(c),.safe_hold(p),.master_hold(h[1]),.slave_open(s[1]),.delayed_ref(cd[1]),.tap4(t4[1]),.tap8(t8[1]),.tap12(t12[1]),.tap16(t16[1]),.h_raw(hr[1]),.s_raw(sr[1]));
 swc_ff16_phasegen #(.TAP_STAGES(12))u12(.clk_ref(c),.safe_hold(p),.master_hold(h[2]),.slave_open(s[2]),.delayed_ref(cd[2]),.tap4(t4[2]),.tap8(t8[2]),.tap12(t12[2]),.tap16(t16[2]),.h_raw(hr[2]),.s_raw(sr[2]));
 swc_ff16_phasegen #(.TAP_STAGES(16))u16(.clk_ref(c),.safe_hold(p),.master_hold(h[3]),.slave_open(s[3]),.delayed_ref(cd[3]),.tap4(t4[3]),.tap8(t8[3]),.tap12(t12[3]),.tap16(t16[3]),.h_raw(hr[3]),.s_raw(sr[3]));
 initial begin
  for(i=0;i<8;i=i+1)begin {sel,a,b}=i[2:0];#1;if(y!==(sel?b:a))$fatal(1,"FF16_PRIMITIVE_TRUTH");vectors=vectors+1;end
  for(i=0;i<4;i=i+1)begin {c,p}=i[1:0];#1;
   for(n=0;n<4;n=n+1)begin
    if(h[n] !== (p?1'b1:c) || s[n] !== (p?1'b0:c) || cd[n]!==c || {t4[n],t8[n],t12[n],t16[n],hr[n],sr[n]}!=={6{c}})$fatal(1,"FF16_UNTIMED_TRUTH");vectors=vectors+1;
   end
   if({u4.u_delay16.y,u8.u_delay16.y,u12.u_delay16.y,u16.u_delay16.y}!=={4{c}})$fatal(1,"FF16_TAIL_MISSING");
  end
  $display("FF16_STATIC_LOGIC_VERIFIED vectors=%0d all_four_taps=1 unselected_tail_present=1 no_deadtime_claim=1",vectors);$finish;
 end
endmodule
