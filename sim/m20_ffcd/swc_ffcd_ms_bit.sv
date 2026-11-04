`timescale 1ns/1ps
// Same two-feedback-MUX model as FF16 B, with independently parameterized leaves.
module swc_ffcd_ms_bit #(parameter integer INDEX=0,parameter bit LOGIC_ONLY=0)
(input wire master_hold,slave_open,d,checks_enable,output wire q,qm,me,se);
 localparam real BUFFER=1.0+3.0*INDEX/32.0;
 localparam real EFFECTIVE=1.0+4.0*INDEX/32.0;
 wire m_pin,s_pin;
 assign #(BUFFER,BUFFER)m_pin=master_hold;
 assign #(BUFFER,BUFFER)s_pin=slave_open;
 swc_ff16_latch_pair pair(.h(m_pin),.s(s_pin),.d(d),.m_open(EFFECTIVE),.m_close(EFFECTIVE),.s_open(EFFECTIVE),.s_close(EFFECTIVE),
 .m_data_r(LOGIC_ONLY?0.0:0.1),.m_data_f(LOGIC_ONLY?0.0:0.1),.s_data_r(LOGIC_ONLY?0.0:0.1),.s_data_f(LOGIC_ONLY?0.0:0.1),.q(q),.qm(qm),.me(me),.se(se));
 integer overlap_events=0;
 always @(me or se)begin #1ps;if(checks_enable && me===0 && se===1)begin overlap_events=overlap_events+1;$fatal(1,"FFCD_OWN_OVERLAP");end end
 always @(q)if(checks_enable&&!$isunknown(q)&&se===0)$fatal(1,"FFCD_STATE_CHANGED_CLOSED");
endmodule
