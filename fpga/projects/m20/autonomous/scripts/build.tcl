# M20 V3: independent board implementation; no programming or Flash operation.
proc main {} {
 global argv swc
 source [file join [file dirname [info script]] ../../../../common/tcl/repo_paths.tcl]
 set root [swc_repo_root [info script]]
 source [file join $root fpga boards swcell_k325t board.tcl]
 if {$swc(part) ne "xc7k325tffg900-2"||$swc(clk_hz)!=50000000} {error "Review V3 constraints for this board part/clock"}
 set stage bitstream;set output "";set rom ""
 foreach {key value} $argv {
  switch -- $key {--stage {set stage $value} --output {set output $value} --rom {set rom $value} default {error "Unknown argument $key"}}
 }
 if {$stage ni {synth bitstream}} {error "Invalid stage"}
 if {$output eq "" || $rom eq ""} {error "Explicit fresh --output and --rom required"}
 set output [file normalize $output];set rom [file normalize $rom]
 if {![string match "[file join $root build]/*" $output]||[file exists $output]} {error "Choose fresh output under build/"}
 if {![file isfile $rom]} {error "Missing ROM"}
 file mkdir $output
 set sources {}
 foreach n {swc_input_sync swc_power_on_reset swc_debounce swc_uart_rx swc_uart_tx swc_uart_hex_json} {lappend sources [file join $root rtl common ${n}.sv]}
 set v3 [file join $root rtl modules m20 v3]
 lappend sources [file join $v3 swc_v3_mux157.sv] [file join $v3 generated m20v3_cpu_core.sv]
 foreach n {swc_m20_v31_memory swc_m20_v31_service swc_m20_v31_gpio} {lappend sources [file join $root rtl modules m20 v31 ${n}.sv]}
 lappend sources [file join $root fpga projects m20 autonomous rtl swcell_m20_v31_top.sv]
 set xdc [file join $root fpga projects diagnostics oled_keys constraints io.xdc]
 set inputs [concat $sources [list $xdc [info script] $rom [file join $root fpga boards swcell_k325t board.tcl]]]
 set hashes [dict create];set f [open [file join $output source_sha256.txt] w]
 foreach file $inputs {
  set file [file normalize $file]
  set digest [lindex [exec sha256sum $file] 0];dict set hashes $file $digest
  puts $f "$digest  [string range $file [expr {[string length $root]+1}] end]"
 };close $f
 create_project -in_memory -part $swc(part)
 set_property verilog_define {SWC_V3_XILINX} [current_fileset]
 foreach file $sources {read_verilog -sv $file}
 set f [open [file join $output software_profile.txt] w];puts $f "ROM_FILE=$rom";close $f
 synth_design -top swcell_m20_v31_top -part $swc(part) -flatten_hierarchy none -generic [list ROM_FILE=$rom]
 read_xdc $xdc
 create_clock -name sys_clk -period 20.0 [get_ports sys_clk]
 set_output_delay -clock sys_clk -max 5.0 [all_outputs]
 set_output_delay -clock sys_clk -min 0.0 [all_outputs]
 set first [get_pins -hier -quiet -regexp {.*(sync_keys|reset_sync|rx_sync|sync_inputs)/pipe_reg\[0\].*/D}]
 if {[llength $first]!=9} {error "Expected six GPI plus reset/debug/RX first synchronizers, got [llength $first]"}
 set_false_path -from [get_ports {RST_N KEY0 KEY1 KEY2 KEY3 KEY5 KEY6 KEY7 UART_RXD}] -to $first
 # No false paths or unconstrained fabric clocks in CPU logic. Try ordinary 50MHz STA first.
 set muxes [get_cells -hier -filter {REF_NAME == LUT3 && NAME =~ *cpu*cell_mux}]
 set expected 477
 if {[llength $muxes]!=$expected} {error "CPU mux mapping differs: [llength $muxes], expected $expected"}
 set f [open [file join $output cpu_mux_cells.txt] w];foreach cell $muxes {puts $f $cell};close $f
 report_utilization -hierarchical -file [file join $output synth_utilization.rpt]
 report_timing_summary -report_unconstrained -file [file join $output synth_timing.rpt]
 report_drc -checks [get_drc_checks LUTLP-1] -file [file join $output feedback_drc.rpt]
 if {$stage eq "synth"} {puts "M20_V31_SYNTH_COMPLETE mode=FUNCTIONAL_STORAGE muxes=[llength $muxes]";return}
 opt_design
 place_design
 route_design
 report_timing_summary -report_unconstrained -file [file join $output timing.rpt]
 report_utilization -hierarchical -file [file join $output utilization.rpt]
 if {[llength [info commands report_ram_utilization]]} {report_ram_utilization -file [file join $output ram.rpt]}
 report_io -file [file join $output io.rpt]
 report_cdc -details -file [file join $output cdc.rpt]
 report_drc -file [file join $output drc.rpt]
 write_checkpoint [file join $output routed.dcp]
 set violations [get_drc_violations -quiet]
 if {[llength $violations]} {error "DRC_BLOCKED_FUNCTIONAL_STORAGE: [llength $violations] violations; no bitstream; see drc.rpt"}
 foreach type {max min} {
  set p [get_timing_paths -delay_type $type -max_paths 1]
  if {[llength $p]!=1||[get_property SLACK $p]<0} {error "FPGA_TIMING_FAILED_$type; no bitstream"}
 }
 # Retain explicit check_timing evidence; clocked native storage is all in sys_clk.
 check_timing -verbose -file [file join $output check_timing.rpt]
 dict for {file digest} $hashes {if {[lindex [exec sha256sum $file] 0] ne $digest} {error "SOURCE_CHANGED_DURING_BUILD $file"}}
 set_property BITSTREAM.STARTUP.STARTUPCLK JTAGCLK [current_design]
 set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]
 write_bitstream [file join $output swcell_m20_v31_top.bit]
 puts "M20_V31_BITSTREAM_PASS $output/swcell_m20_v31_top.bit"
}
if {[catch {main} message]} {puts stderr "M20_V31_BUILD_ERROR: $message";exit 1}
exit 0
