`timescale 1ns/1ps
module tb_ff16_model;
 logic sel=0,a=0,b=0;real dr=2,df=3,sr=5,sf=7;wire y,se;
 swc_ff16_mux_timing mux(.s(sel),.i0(a),.i1(b),.dr(dr),.df(df),.sr(sr),.sf(sf),.y(y),.effective_s(se));
 logic h=0,s=0,d=0;wire q,qm,me,sle;
 real m_open=1,m_close=5,s_open=1,s_close=5,dd=0.1;
 swc_ff16_latch_pair ff(.h(h),.s(s),.d(d),.m_open(m_open),.m_close(m_close),.s_open(s_open),.s_close(s_close),.m_data_r(dd),.m_data_f(dd),.s_data_r(dd),.s_data_f(dd),.q(q),.qm(qm),.me(me),.se(sle));
 initial begin
  #20;if(y!==0)$fatal(1,"MODEL_INITIAL");
  a=1;#1.9;if(y!==0)$fatal(1,"MODEL_DATA_EARLY");#0.2;if(y!==1)$fatal(1,"MODEL_DATA_RISE");
  a=0;#2.9;if(y!==1)$fatal(1,"MODEL_DATA_FALL_EARLY");#0.2;if(y!==0)$fatal(1,"MODEL_DATA_FALL");
  a=1;#1;a=0;#5;if(y!==0)$fatal(1,"MODEL_INERTIAL_FILTER");
  b=1;#3;sel=1;#4.9;if(y!==0)$fatal(1,"MODEL_SELECT_EARLY");#0.2;if(y!==1)$fatal(1,"MODEL_SELECT_RISE");
  sel=0;#6.9;if(y!==1)$fatal(1,"MODEL_SELECT_FALL_EARLY");#0.2;if(y!==0)$fatal(1,"MODEL_SELECT_FALL");
  // Initialize actual two feedback muxes by complete transparent/hold phases.
  h=1;#10;s=1;#10;s=0;#10;h=0;#10;
  if(q!==0 || qm!==0)$fatal(1,"MODEL_FF_INIT");
  h=1;#1;s=1;#2;d=1;#0.4;
  if(me!==0 || sle!==1 || q!==1)$fatal(1,"MODEL_RISE_PENETRATION_NOT_OBSERVED");
  #10;s=0;#1;h=0;#2;d=0;#0.4;
  if(me!==0 || sle!==1 || q!==0)$fatal(1,"MODEL_FALL_PENETRATION_NOT_OBSERVED");
  $display("FF16_PIN_MODEL_VERIFIED data_rise_fall=1 select_rise_fall=1 inertial_short_pulse=1 actual_penetration_directions=2");$finish;
 end
 initial begin #10000;$fatal(1,"MODEL_WATCHDOG");end
endmodule
