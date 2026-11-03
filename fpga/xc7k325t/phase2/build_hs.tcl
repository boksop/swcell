# Usage: vivado -mode batch -source build_hs.tcl -tclargs Hz Qphase QMphase bits pattern scan outdir
# Phase indices are 0..15. This script never programs hardware or Flash.
proc write_status {out status reason} {
 set h [open [file join $out build_status.json] w]
 puts $h "{\"status\":\"$status\",\"reason\":\"$reason\"}"
 close $h
}
proc run {} {
 global argv
 if {[llength $argv]!=7} {error "Expected Hz Qphase QMphase bits pattern scan outdir"}
 lassign $argv hz qphase mphase bits pattern scan out
 set root [file normalize [file join [file dirname [info script]] ../../..]]
 set out [file normalize $out];file mkdir $out
 set plans [dict create 1000000 {0 0} 5000000 {12 120} 10000000 {16 80} 25000000 {16 32} 50000000 {16 16} 75000000 {24 16} 100000000 {16 8} 125000000 {20 8} 150000000 {24 8} 200000000 {24 6}]
 if {![dict exists $plans $hz]} {write_status $out UNSUPPORTED FREQUENCY_PLAN;return}
 foreach n [list $qphase $mphase] {if {![string is integer -strict $n] || $n<0 || $n>15} {error "Phase index must be 0..15"}}
 if {![string is wideinteger -strict $bits] || $bits<1 || $bits>1000000000} {error "bits must be 1..1000000000"}
 if {$pattern ni {0 1 2 3 5} || $scan ni {0 1}} {error "pattern=0,1,2,3,5; scan=0|1"}
 lassign [dict get $plans $hz] mult divide
 create_project -in_memory -part xc7k325tffg900-2
 foreach file [glob [file join $root rtl common *.sv]] {read_verilog -sv $file}
 foreach file [glob [file join $root rtl common xilinx *.sv]] {read_verilog -sv $file}
 foreach file [glob [file join $root rtl modules m11 phase2 *.sv]] {read_verilog -sv $file}
 read_verilog -sv [file join $root fpga xc7k325t phase2 swcell_m11_hs_top.sv]
 set timeout [expr {wide(50000000)*(5+($bits+$hz-1)/$hz)}]
 set generics [list FREQUENCY_HZ=$hz MULT=$mult DIVIDE=$divide Q_PHASE=$qphase QM_PHASE=$mphase BITS=$bits PATTERN=$pattern SCAN=$scan TIMEOUT_CYCLES=$timeout]
 synth_design -top swcell_m11_hs_top -part xc7k325tffg900-2 -generic $generics
 read_xdc [file join $root fpga xc7k325t constraints board_50mhz.xdc]
 create_clock -name sys_clk -period 20 [get_ports sys_clk]
 if {$hz==1000000} {
   create_generated_clock -name dut_clock_out -source [get_ports sys_clk] -divide_by 50 [get_ports M11_DFF_CLK]
 } else {
   set forward_c [get_pins -hier -filter {REF_PIN_NAME == C && NAME =~ *forward_clock*}]
   if {[llength $forward_c]!=1} {error "Expected one ODDR forward clock pin"}
   create_generated_clock -name dut_clock_out -source $forward_c -divide_by 1 [get_ports M11_DFF_CLK]
 }
 # These two inputs are intentionally characterized by phase scanning, not STA.
 # No PCB or 157 min/max timing has been supplied. Exempt ONLY pad -> IOB D.
 # Internal captured Q -> comparator and every expected-data path remain timed.
 foreach {port lane} {M11_DFF_Q q_lane M11_DFF_QM qm_lane} {
   set cap [get_pins -hier -quiet -regexp ".*engine/$lane/captured_reg/D"]
   if {[llength $cap]!=1} {error "Expected one IOB capture D pin for $port"}
   set_false_path -from [get_ports $port] -to $cap
 }
 # Bundled payloads are held indefinitely after done; bridge waits >=4 sys clocks.
 foreach lane {q qm} {
   set pattern_re [format {.*engine/%s_lane/(total_bits|errors|first_.*|start_state)_reg(\[[0-9]+\])?$} $lane]
   set src [filter [get_cells -hier -quiet -regexp $pattern_re] {IS_SEQUENTIAL == 1}]
   set dst [get_cells -hier -quiet -regexp ".*${lane}_bridge/payload_reg.*"]
   if {[llength $src]==0 || [llength $dst]==0} {error "Snapshot path missing"}
   set_max_delay -datapath_only 20 -from $src -to $dst
 }
 set sync_first [get_pins -hier -quiet -regexp {.*(done_sync_reg\[0\]|pipe_reg\[0\].*)/D}]
 if {[llength $sync_first]} {set_false_path -to $sync_first}
 # ASYNC_REG reset synchronizers assert asynchronously and release only after
 # two destination edges. The raw reset is NOT synchronous to these PRE pins.
 # Same endpoint scope as XPM_CDC_ASYNC_RST's local recovery/removal exception;
 # never cut the synchronizer's Q->D chain or its downstream reset/data paths.
 set reset_pre [get_pins -hier -quiet -regexp {engine/r[bdqm]/reset_pipe_reg\[[01]\]/PRE}]
 if {[llength $reset_pre]<2 || [llength $reset_pre]>8} {error "Missing reset synchronizer PRE endpoints"}
 set_false_path -to $reset_pre
 set_property BITSTREAM.STARTUP.STARTUPCLK JTAGCLK [current_design]
 set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]
 opt_design;place_design;route_design
 report_timing_summary -report_unconstrained -file [file join $out timing.rpt]
 report_clock_interaction -file [file join $out clock_interaction.rpt]
 report_cdc -details -file [file join $out cdc.rpt]
 report_utilization -file [file join $out utilization.rpt]
 report_io -file [file join $out io.rpt]
 report_drc -file [file join $out drc.rpt]
 write_checkpoint -force [file join $out routed.dcp]
 # Machine-readable routed evidence; no external IO delay is inferred here.
 set h [open [file join $out timing.rpt] r];set timing_text [read $h];close $h
 if {![regexp {WNS\(ns\)[^\n]*\n[^\n]*\n\s*([-0-9.]+)\s+[-0-9.]+\s+[0-9]+\s+[0-9]+\s+([-0-9.]+)\s+[-0-9.]+\s+[0-9]+\s+[0-9]+\s+([-0-9.]+)} $timing_text _ wns whs wpws]} {error "Cannot parse timing summary"}
 set qloc [get_property LOC [get_cells engine/q_lane/captured_reg]]
 set mloc [get_property LOC [get_cells engine/qm_lane/captured_reg]]
 set h [open [file join $out timing_metrics.json] w]
 puts $h "{\"wns_ns\":$wns,\"whs_ns\":$whs,\"wpws_ns\":$wpws,\"q_capture_loc\":\"$qloc\",\"qm_capture_loc\":\"$mloc\",\"external_delays_calibrated\":false}"
 close $h
 if {[llength [get_drc_violations -quiet]]} {write_status $out BUILD_ERROR DRC;error "DRC failed"}
 if {$wpws<0} {write_status $out UNSUPPORTED FPGA_PULSE_WIDTH;return}
 foreach delay {max min} {
   set path [get_timing_paths -quiet -delay_type $delay -max_paths 1]
   if {[llength $path]==0} {error "No timing paths found"}
   if {[get_property SLACK $path]<0} {write_status $out UNSUPPORTED FPGA_TIMING;return}
 }
 # Prove the data capture FFs physically use ILOGIC, not a fabric register.
 foreach lane {q_lane qm_lane} {
   set loc [get_property LOC [get_cells engine/$lane/captured_reg]]
   if {![string match ILOGIC* $loc]} {error "$lane capture not placed in ILOGIC: $loc"}
 }
 write_bitstream -force [file join $out swcell_m11_hs_top.bit]
 write_status $out SUPPORTED INTERNAL_TIMING_PASS_EXTERNAL_DELAYS_UNCALIBRATED
 puts "SWCELL_HS_BUILD_PASS $hz $qphase $mphase $bits"
}
if {[catch {run} message]} {puts stderr "SWCELL_HS_BUILD_ERROR $message";exit 1}
exit 0
