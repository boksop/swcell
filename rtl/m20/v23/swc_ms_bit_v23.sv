`timescale 1ns/1ps
// Digital pin-delay experiment, not transistor/metastability or NC7SZ157 timing signoff.
module swc_mux157_v23 #(parameter real DATA_NS=0.0,SELECT_NS=0.0)
(input wire s,i0,i1,output wire y);
 wire s_eff,a_eff,b_eff;
 assign #(SELECT_NS) s_eff=s;
 assign #(DATA_NS) a_eff=i0;
 assign #(DATA_NS) b_eff=i1;
 assign y=s_eff?b_eff:a_eff;
endmodule
module swc_ms_bit_v23 #(
 parameter real DATA_NS=0.0,SELECT_NS=0.0,MASTER_NS=0.0,SLAVE_NS=0.0,
 parameter bit CHECK_FATAL=1
)(input wire master_hold,slave_open,d,checks_enable,output wire q,qm);
 wire m_pin,s_pin;
 assign #(MASTER_NS) m_pin=master_hold;
 assign #(SLAVE_NS) s_pin=slave_open;
 swc_mux157_v23 #(.DATA_NS(DATA_NS),.SELECT_NS(SELECT_NS)) master(.s(m_pin),.i0(d),.i1(qm),.y(qm));
 swc_mux157_v23 #(.DATA_NS(DATA_NS),.SELECT_NS(SELECT_NS)) slave(.s(s_pin),.i0(q),.i1(qm),.y(q));
 // Verification-only monitors; not CPU storage or part of physical MUX budget.
 integer overlap_events=0,closed_changes=0;
 always @(master.s_eff or slave.s_eff)begin
  #1ps;
  if(checks_enable && master.s_eff===0 && slave.s_eff===1)begin
   overlap_events=overlap_events+1;
   if(CHECK_FATAL)$fatal(1,"V23_PHASE_OVERLAP %m");
  end
 end
 always @(q)begin
  if(checks_enable && !$isunknown(q) && slave.s_eff===0)begin
   closed_changes=closed_changes+1;
   if(CHECK_FATAL)$fatal(1,"V23_STATE_CHANGED_SLAVE_CLOSED %m");
  end
 end
endmodule
