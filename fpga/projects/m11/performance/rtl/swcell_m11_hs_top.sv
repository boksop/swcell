`default_nettype none
module swcell_m11_hs_top #(
 parameter integer FREQUENCY_HZ=25000000,MULT=16,DIVIDE=32,
 parameter integer Q_PHASE=4,QM_PHASE=12,PATTERN=5,SCAN=1,
 parameter integer UART_BAUD=115200,POR_CYCLES=5000000,
 parameter [63:0] BITS=64'd1000000,TIMEOUT_CYCLES=64'd1000000000
)(input wire sys_clk,UART_RXD,
 output wire UART_TX,LED_G,LED_Y,LED_R,
 output wire M11_DL_D,M11_DL_EN,M11_DFF_D,M11_DFF_CLK,
 input wire M11_DL_Q,M11_DFF_Q,M11_DFF_QM);
 wire por;
 swc_power_on_reset #(.HOLD_CYCLES(POR_CYCLES)) power_on_reset(.clk(sys_clk),.rst(por));
 wire bc,dc,qc,mc,bce,dce,qce,mce,locked;
 reg stop;
 swc_hs_clocks #(.FREQUENCY_HZ(FREQUENCY_HZ),.MULT(MULT),.DIVIDE(DIVIDE),
   .Q_PHASE(Q_PHASE),.QM_PHASE(QM_PHASE)) clocks(.sys_clk(sys_clk),.rst(por || stop),
   .base_clk(bc),.d_clk(dc),.q_clk(qc),.qm_clk(mc),.base_ce(bce),.d_ce(dce),
   .q_ce(qce),.qm_ce(mce),.locked(locked),.clock_pin(M11_DFF_CLK));
 wire q_done,m_done;wire [255:0] qp,mp,q_snap,m_snap;
 wire q_valid,m_valid;
 wire q_error_event,qm_error_event; // Extension points for a future ring buffer.
 m11_hs_engine #(.Q_PHASE(Q_PHASE),.QM_PHASE(QM_PHASE),.PATTERN(PATTERN),.BITS(BITS)) engine(
   .base_clk(bc),.d_clk(dc),.q_clk(qc),.qm_clk(mc),.reset_n(!por && locked && !stop),
   .base_ce(bce),.d_ce(dce),.q_ce(qce),.qm_ce(mce),.q_in(M11_DFF_Q),.qm_in(M11_DFF_QM),
   .data_pin(M11_DFF_D),.q_payload(qp),.qm_payload(mp),.q_done(q_done),.qm_done(m_done),
   .q_error_event(q_error_event),.qm_error_event(qm_error_event));
 swc_snapshot_bridge #(.WIDTH(256)) q_bridge(.clk(sys_clk),.rst(por),
   .source_done(q_done),.source_payload(qp),.valid(q_valid),.payload(q_snap));
 swc_snapshot_bridge #(.WIDTH(256)) qm_bridge(.clk(sys_clk),.rst(por),
   .source_done(m_done),.source_payload(mp),.valid(m_valid),.payload(m_snap));
 wire [63:0] qt,qe,qf,mt,me,mf;wire qx,qa,mx,ma;wire [30:0] qs,ms,qstart,mstart;
 assign {qt,qe,qf,qx,qa,qs,qstart}=q_snap;
 assign {mt,me,mf,mx,ma,ms,mstart}=m_snap;
 wire choose_q=qe!=0 && (me==0 || qf<=mf);
 wire [63:0] first_cycle=choose_q?qf:mf;
 wire [63:0] first_lane=(qe==0 && me==0)?64'd0:(choose_q?64'd1:64'd2);
 wire [63:0] first_expected={63'b0,(choose_q?qx:mx)};
 wire [63:0] first_actual={63'b0,(choose_q?qa:ma)};
 wire [63:0] first_state={33'b0,(choose_q?qs:ms)};
 function automatic [127:0] hex64(input [63:0] value);
   integer i;reg [3:0] n;
   begin for(i=0;i<16;i=i+1) begin
     n=value[(15-i)*4+:4];hex64[(15-i)*8+:8]=(n<10)?(8'd48+{4'b0,n}):(8'd87+{4'b0,n});
   end end
 endfunction
 localparam integer BODY_LEN=1289;
 wire [BODY_LEN*8-1:0] body={
   "\"protocol_version\":2,\"module\":\"M11\",\"device\":\"74LVC1G157\",\"test\":\"",(PATTERN==5?"PRBS_STABILITY":"DFF_HS_PATTERN"),"\",\"fpga_version\":\"m11_hs_v2_2\",\"phase_units\":\"turn/16\",\"voltage_v\":null,\"temperature_c\":null,\"voltage_nominal_v\":3.3,\"idelay_tap\":null,\"pcb_delay_ns\":null,",
   "\"frequency_hz\":\"0x",
   hex64(64'(FREQUENCY_HZ)),
   "\",",
   "\"d_phase\":\"0x",
   hex64(64'(4)),
   "\",",
   "\"q_sample_phase\":\"0x",
   hex64(64'(Q_PHASE)),
   "\",",
   "\"qm_sample_phase\":\"0x",
   hex64(64'(QM_PHASE)),
   "\",",
   "\"d_phase_mdeg\":\"0x",
   hex64(64'((FREQUENCY_HZ==1000000)?93600:90000)),
   "\",",
   "\"q_phase_mdeg\":\"0x",
   hex64(64'((FREQUENCY_HZ==1000000)?((Q_PHASE*50+8)/16)*7200:Q_PHASE*22500)),
   "\",",
   "\"qm_phase_mdeg\":\"0x",
   hex64(64'((FREQUENCY_HZ==1000000)?((QM_PHASE*50+8)/16)*7200:QM_PHASE*22500)),
   "\",",
   "\"pattern\":\"0x",
   hex64(64'(PATTERN)),
   "\",",
   "\"requested_bits\":\"0x",
   hex64(BITS),
   "\",",
   "\"total_bits\":\"0x",
   hex64(qt),
   "\",",
   "\"qm_total_bits\":\"0x",
   hex64(mt),
   "\",",
   "\"q_errors\":\"0x",
   hex64(qe),
   "\",",
   "\"qm_errors\":\"0x",
   hex64(me),
   "\",",
   "\"q_first_error_cycle\":\"0x",
   hex64(qf),
   "\",",
   "\"qm_first_error_cycle\":\"0x",
   hex64(mf),
   "\",",
   "\"first_error_cycle\":\"0x",
   hex64(first_cycle),
   "\",",
   "\"first_error_lane\":\"0x",
   hex64(first_lane),
   "\",",
   "\"first_error_expected\":\"0x",
   hex64(first_expected),
   "\",",
   "\"first_error_actual\":\"0x",
   hex64(first_actual),
   "\",",
   "\"q_first_expected\":\"0x",
   hex64({63'b0,qx}),
   "\",",
   "\"q_first_actual\":\"0x",
   hex64({63'b0,qa}),
   "\",",
   "\"qm_first_expected\":\"0x",
   hex64({63'b0,mx}),
   "\",",
   "\"qm_first_actual\":\"0x",
   hex64({63'b0,ma}),
   "\",",
   "\"prbs_state\":\"0x",
   hex64(first_state),
   "\",",
   "\"q_first_state\":\"0x",
   hex64({33'b0,qs}),
   "\",",
   "\"qm_first_state\":\"0x",
   hex64({33'b0,ms}),
   "\",",
   "\"q_start_state\":\"0x",
   hex64({33'b0,qstart}),
   "\",",
   "\"qm_start_state\":\"0x",
   hex64({33'b0,mstart}),
   "\","};
 reg [3:0] state;reg aborted,saw_lock;
 reg [63:0] watchdog;
 wire ready,byte_ready,byte_valid;wire [7:0] byte_data;
 reg [2048*8-1:0] packet;
 reg [11:0] length;
 wire request=state==0 || state==3 || state==5 || state==7;
 wire bad=qe!=0 || me!=0;
 // Payload data is immutable after bridge capture. Packet sender additionally snapshots.
 always @* begin
   packet=0;length=0;
   if(state==0) begin
     packet={"{\"type\":\"SWEEP_START\",",body,"\"status\":\"RUNNING\"}\n"};
     length=12'(22+BODY_LEN+20);
   end else if(state==3) begin
     if(aborted) begin
       packet={"{\"type\":\"FREQ_RESULT\",",body,"\"status\":\"ABORTED\"}\n"};
       length=12'(22+BODY_LEN+20);
     end else if(SCAN!=0) begin
       if(bad) begin
         packet={"{\"type\":\"PHASE_RESULT\",",body,"\"status\":\"CAPTURE_ERRORS\"}\n"};
         length=12'(23+BODY_LEN+27);
       end else begin
         packet={"{\"type\":\"PHASE_RESULT\",",body,"\"status\":\"PASS\"}\n"};
         length=12'(23+BODY_LEN+17);
       end
     end else if(bad) begin
       packet={"{\"type\":\"FREQ_RESULT\",",body,"\"status\":\"CAPTURE_ERRORS\"}\n"};
       length=12'(22+BODY_LEN+27);
     end else begin
       packet={"{\"type\":\"FREQ_RESULT\",",body,"\"status\":\"PASS\"}\n"};
       length=12'(22+BODY_LEN+17);
     end
   end else if(state==5) begin
     packet={"{\"type\":\"ERROR_SNAPSHOT\",",body,"\"status\":\"CAPTURE_ERRORS\"}\n"};
     length=12'(25+BODY_LEN+27);
   end else begin
     if(aborted) begin
       packet={"{\"type\":\"SWEEP_COMPLETE\",",body,"\"status\":\"ABORTED\"}\n"};
       length=12'(25+BODY_LEN+20);
     end else if(bad) begin
       packet={"{\"type\":\"SWEEP_COMPLETE\",",body,"\"status\":\"CAPTURE_ERRORS\"}\n"};
       length=12'(25+BODY_LEN+27);
     end else begin
       packet={"{\"type\":\"SWEEP_COMPLETE\",",body,"\"status\":\"PASS\"}\n"};
       length=12'(25+BODY_LEN+17);
     end
   end
 end
 swc_json_packet_tx sender(.clk(sys_clk),.rst(por),.request(request),.packet(packet),
   .byte_count(length),.ready(ready),.tx_valid(byte_valid),.tx_ready(byte_ready),.tx_data(byte_data));
 swc_uart_tx #(.CLK_HZ(50000000),.BAUD(UART_BAUD)) uart(.clk(sys_clk),.rst(por),
   .data(byte_data),.valid(byte_valid),.ready(byte_ready),.tx(UART_TX));
 wire lock_sync;
 swc_input_sync #(.WIDTH(1)) lock_sampler(.clk(sys_clk),.rst(por),.async_in(locked),.sync_out(lock_sync));
 always @(posedge sys_clk) begin
   if(por) begin state<=0;stop<=0;aborted<=0;saw_lock<=0;watchdog<=0;end
   else begin
     if(lock_sync) saw_lock<=1;
     if(!stop) begin
       watchdog<=watchdog+1'b1;
       if(q_valid && m_valid) stop<=1;
       else if(watchdog>=TIMEOUT_CYCLES || (saw_lock && !lock_sync)) begin stop<=1;aborted<=1;end
     end
     case(state)
       0:if(ready) state<=1;
       1:if(ready && byte_ready) state<=2;
       2:if(stop) state<=3;
       3:if(ready) state<=4;
       4:if(ready && byte_ready) state<=(!aborted && bad)?5:7;
       5:if(ready) state<=6;
       6:if(ready && byte_ready) state<=7;
       7:if(ready) state<=8;
       8:if(ready && byte_ready) state<=9;
       default:state<=9;
     endcase
   end
 end
 assign LED_G=state==9 && !aborted && !bad;
 assign LED_Y=!por && state!=9;
 assign LED_R=state==9 && (aborted || bad);
 assign M11_DL_D=0;assign M11_DL_EN=1;
endmodule
`default_nettype wire
