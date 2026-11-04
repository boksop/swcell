`timescale 1ns/1ps
// Simulation-only pin-path inertial model. Each pin transition cancels a pending
// transition on that same delayed pin when its input pulse is too short.
// Boolean mux selection follows delayed pins with delta-cycle propagation.
// No transistor/metastability, analog RC or calibrated tcd claim.
module swc_ff16_mux_timing(
 input wire s,i0,i1,
 input real dr,df,sr,sf,
 output wire y,output wire effective_s
);
 wire a,b;
 assign #(sr,sf) effective_s=s;
 assign #(dr,df) a=i0;
 assign #(dr,df) b=i1;
 assign y=effective_s?b:a;
endmodule

module swc_ff16_phase_timing #(parameter integer TAP_STAGES=8)(
 input wire clk_ref,safe_hold,
 input real dr[0:19],df[0:19],sr[0:19],sf[0:19],
 output wire master_hold,slave_open,delayed_ref,tap4,tap8,tap12,tap16,h_raw,s_raw
);
 wire [16:0] chain;
 assign chain[0]=clk_ref;
 for(genvar i=0;i<16;i=i+1)begin:g_delay
  swc_ff16_mux_timing u(.s(1'b0),.i0(chain[i]),.i1(1'b0),.dr(dr[i]),.df(df[i]),.sr(sr[i]),.sf(sf[i]),.y(chain[i+1]),.effective_s());
 end
 assign tap4=chain[4];assign tap8=chain[8];assign tap12=chain[12];assign tap16=chain[16];
 generate if(TAP_STAGES==4)assign delayed_ref=tap4;
 else if(TAP_STAGES==8)assign delayed_ref=tap8;
 else if(TAP_STAGES==12)assign delayed_ref=tap12;
 else if(TAP_STAGES==16)assign delayed_ref=tap16;
 else begin initial $fatal(1,"FF16_BAD_TAP");end endgenerate
 swc_ff16_mux_timing h(.s(clk_ref),.i0(delayed_ref),.i1(1'b1),.dr(dr[16]),.df(df[16]),.sr(sr[16]),.sf(sf[16]),.y(h_raw),.effective_s());
 swc_ff16_mux_timing s(.s(clk_ref),.i0(1'b0),.i1(delayed_ref),.dr(dr[17]),.df(df[17]),.sr(sr[17]),.sf(sf[17]),.y(s_raw),.effective_s());
 swc_ff16_mux_timing ph(.s(safe_hold),.i0(h_raw),.i1(1'b1),.dr(dr[18]),.df(df[18]),.sr(sr[18]),.sf(sf[18]),.y(master_hold),.effective_s());
 swc_ff16_mux_timing ps(.s(safe_hold),.i0(s_raw),.i1(1'b0),.dr(dr[19]),.df(df[19]),.sr(sr[19]),.sf(sf[19]),.y(slave_open),.effective_s());
endmodule

module swc_ff16_latch_pair(
 input wire h,s,d,
 input real m_open,m_close,s_open,s_close,m_data_r,m_data_f,s_data_r,s_data_f,
 output wire q,qm,me,se
);
 swc_ff16_mux_timing master(.s(h),.i0(d),.i1(qm),.dr(m_data_r),.df(m_data_f),.sr(m_close),.sf(m_open),.y(qm),.effective_s(me));
 swc_ff16_mux_timing slave(.s(s),.i0(q),.i1(qm),.dr(s_data_r),.df(s_data_f),.sr(s_open),.sf(s_close),.y(q),.effective_s(se));
endmodule

module swc_ff16_path_delay(input wire a,input real rise_ns,fall_ns,output wire y);
 assign #(rise_ns,fall_ns)y=a;
endmodule
