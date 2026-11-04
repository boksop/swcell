# Standalone GPIO/OLED diagnostic. Never programs hardware or accesses Flash.
proc main {} {
 global argv swc
 source [file join [file dirname [info script]] ../../../../common/tcl/repo_paths.tcl]
 set root [swc_repo_root [info script]]
 source [file join $root fpga boards swcell_k325t board.tcl]
 set stage bitstream
 if {[llength $argv]} {
  if {[llength $argv]!=2||[lindex $argv 0] ne "--stage"} {error "Usage: --stage synth|bitstream"}
  set stage [lindex $argv 1]
 }
 if {$stage ni {synth bitstream}} {error "Invalid stage"}
 if {$swc(clk_hz)!=50000000} {error "Revalidate diagnostic timing before changing reference clock"}
 set out [file join $root build fpga diagnostics oled_keys]
 file mkdir $out
 # Record and verify input bytes so an interrupted/editing build cannot be accepted silently.
 set inputs [list [info script] [file join $root fpga boards swcell_k325t board.tcl] [file join $root fpga projects diagnostics oled_keys constraints io.xdc]]
 foreach name {swc_input_sync swc_power_on_reset swc_debounce swc_spi_tx swc_uart_tx} {lappend inputs [file join $root rtl common ${name}.sv]}
 lappend inputs [file join $root rtl common display swc_ssd1306.sv]
 foreach file [glob [file join $root fpga projects diagnostics oled_keys rtl *.sv]] {lappend inputs $file}
 set source_hashes [dict create]
 set manifest [open [file join $out source_sha256.txt] w]
 foreach file $inputs {
  set file [file normalize $file]
  set digest [lindex [exec sha256sum $file] 0]
  dict set source_hashes $file $digest
  puts $manifest "$digest  [string range $file [expr {[string length $root]+1}] end]"
 }
 close $manifest
 create_project -in_memory -part $swc(part)
 foreach name {swc_input_sync swc_power_on_reset swc_debounce swc_spi_tx swc_uart_tx} {
  read_verilog -sv [file join $root rtl common ${name}.sv]
 }
 read_verilog -sv [file join $root rtl common display swc_ssd1306.sv]
 foreach name {swc_oled_font_pkg swc_io_diag_pixels swc_io_diag_uart swcell_oled_keys_top} {
  read_verilog -sv [file join $root fpga projects diagnostics oled_keys rtl ${name}.sv]
 }
 synth_design -top swcell_oled_keys_top -part $swc(part)
 read_xdc [file join $root fpga projects diagnostics oled_keys constraints io.xdc]
 create_clock -name sys_clk -period 20.0 [get_ports sys_clk]
 # A conservative FPGA I/O placement budget; not a measured PCB delay or SSD1306 signoff.
 set_output_delay -clock sys_clk -max 5.0 [all_outputs]
 set_output_delay -clock sys_clk -min 0.0 [all_outputs]
 # Only asynchronous pads to the first sync stage are exempt. Downstream chains remain timed.
 set key_first [get_pins -hier -quiet -regexp {.*keys_filter/sync_inputs/pipe_reg\[0\].*/D}]
 set rx_first [get_pins -hier -quiet -regexp {.*rx_watch/pipe_reg\[0\].*/D}]
 if {[llength $key_first]!=9||[llength $rx_first]!=1} {error "Expected 9+1 first-stage synchronizer pins; review actual netlist"}
 set_false_path -from [get_ports {RST_N KEY0 KEY1 KEY2 KEY3 KEY4 KEY5 KEY6 KEY7}] -to $key_first
 set_false_path -from [get_ports UART_RXD] -to $rx_first
 report_utilization -file [file join $out synth_utilization.rpt]
 report_timing_summary -file [file join $out synth_timing.rpt]
 if {$stage eq "synth"} {puts "OLED_KEYS_SYNTH_PASS";return}
 set_property BITSTREAM.STARTUP.STARTUPCLK JTAGCLK [current_design]
 set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]
 foreach port [get_ports] {
  if {[get_property PACKAGE_PIN $port] eq ""||[get_property IOSTANDARD $port] eq "DEFAULT"} {error "Unconstrained pin $port"}
 }
 opt_design
 place_design
 route_design
 report_timing_summary -report_unconstrained -file [file join $out timing.rpt]
 report_utilization -file [file join $out utilization.rpt]
 report_io -file [file join $out io.rpt]
 report_cdc -details -file [file join $out cdc.rpt]
 report_drc -file [file join $out drc.rpt]
 foreach type {max min} {
  set p [get_timing_paths -quiet -delay_type $type -max_paths 1]
  if {[llength $p]!=1||[get_property SLACK $p]<0} {error "FPGA $type timing failed"}
 }
 if {[llength [get_drc_violations -quiet]]} {error "DRC violations; bitstream is not accepted"}
 set h [open [file join $out timing.rpt] r];set text [read $h];close $h
 if {![regexp {WNS\(ns\)[^\n]*\n[^\n]*\n\s*([-0-9.]+)\s+[-0-9.]+\s+[0-9]+\s+[0-9]+\s+([-0-9.]+)\s+[-0-9.]+\s+[0-9]+\s+[0-9]+\s+([-0-9.]+)} $text _ wns whs wpws]} {error "Timing metrics parse failed"}
 if {$wns<0||$whs<0||$wpws<0} {error "Setup/hold/pulse-width failure"}
 write_checkpoint -force [file join $out routed.dcp]
 dict for {file expected} $source_hashes {
  if {[lindex [exec sha256sum $file] 0] ne $expected} {error "SOURCE_CHANGED_DURING_BUILD: $file"}
 }
 write_bitstream -force [file join $out swcell_oled_keys_top.bit]
 set h [open [file join $out build_status.json] w]
 puts $h "{\"status\":\"FPGA_INTERNAL_TIMING_PASS\",\"wns_ns\":$wns,\"whs_ns\":$whs,\"wpws_ns\":$wpws,\"hardware_verified\":false,\"oled_ack_available\":false}"
 close $h
 puts "OLED_KEYS_BITSTREAM_PASS $out/swcell_oled_keys_top.bit"
}
if {[catch {main} message]} {puts stderr "OLED_KEYS_BUILD_ERROR: $message";exit 1}
exit 0
