# M20 V3: independent board implementation; no programming or Flash operation.
proc main {} {
 global argv swc
 source [file join [file dirname [info script]] ../../../../common/tcl/repo_paths.tcl]
 set root [swc_repo_root [info script]]
 source [file join $root fpga boards swcell_k325t board.tcl]
 if {$swc(part) ne "xc7k325tffg900-2"||$swc(clk_hz)!=50000000} {error "Review V3 constraints for this board part/clock"}
 set mode FUNCTIONAL_STORAGE;set stage bitstream;set output "";set test_rom "";set snake_rom "";set snake_done 316
 set snake_done_set 0
 foreach {key value} $argv {
  switch -- $key {--mode {set mode $value} --stage {set stage $value} --output {set output $value} --test-rom {set test_rom $value} --snake-rom {set snake_rom $value} --snake-done {set snake_done $value;set snake_done_set 1} default {error "Unknown argument $key"}}
 }
 if {$mode ni {FUNCTIONAL_STORAGE STRICT_MUX}||$stage ni {synth bitstream}} {error "Invalid V3 mode/stage"}
 if {$output eq ""} {set output [file join $root build fpga m20 cpu_validation $mode]}
 set output [file normalize $output]
 if {![string match "[file join $root build]/*" $output]||[file exists $output]} {error "Choose fresh output under build/"}
 file mkdir $output
 set common {swc_input_sync swc_power_on_reset swc_debounce swc_key_event_buffer swc_spi_tx swc_uart_tx swc_uart_rx swc_uart_hex_json}
 set sources {}
 foreach n $common {lappend sources [file join $root rtl common ${n}.sv]}
 lappend sources [file join $root rtl common display swc_ssd1306.sv]
 lappend sources [file join $root fpga projects diagnostics oled_keys rtl swc_oled_font_pkg.sv]
 set v3 [file join $root rtl modules m20 v3]
 lappend sources [file join $v3 generated m20_v3_game_pkg.sv]
 lappend sources [file join $v3 swc_v3_mux157.sv] [file join $v3 generated m20v3_cpu_core.sv]
 foreach n {swc_m20_v3_memory swc_m20_v3_system swc_m20_v3_display} {lappend sources [file join $v3 ${n}.sv]}
 lappend sources [file join $root fpga projects m20 cpu_validation rtl swcell_m20_v3_top.sv]
 set xdc [file join $root fpga projects diagnostics oled_keys constraints io.xdc]
 set pong [file join $v3 generated pong.memh];set snake [file join $v3 generated snake.memh]
 if {$snake_rom ne ""} {
  if {!$snake_done_set||![string is integer -strict $snake_done]||$snake_done<0||$snake_done>4095} {error "Variant ROM needs explicit --snake-done 0..4095"}
  set snake [file normalize $snake_rom]
  if {![file isfile $snake]} {error "Missing Snake variant ROM"}
 }
 # Diagnostic profile only. Original Pong/Snake files are never overwritten.
 if {$test_rom ne ""} {
  set pong [file normalize $test_rom]
  if {![file isfile $pong]} {error "Missing diagnostic ROM"}
 }
 set inputs [concat $sources [list $xdc [info script] $pong $snake [file join $root fpga boards swcell_k325t board.tcl]]]
 set hashes [dict create];set f [open [file join $output source_sha256.txt] w]
 foreach file $inputs {
  set file [file normalize $file]
  set digest [lindex [exec sha256sum $file] 0];dict set hashes $file $digest
  puts $f "$digest  [string range $file [expr {[string length $root]+1}] end]"
 };close $f
 create_project -in_memory -part $swc(part)
 set_property verilog_define {SWC_V3_XILINX} [current_fileset]
 foreach file $sources {read_verilog -sv $file}
 set f [open [file join $output software_profile.txt] w];puts $f "PONG_FILE=$pong\nSNAKE_FILE=$snake\nSNAKE_TICK_DONE=$snake_done";close $f
 synth_design -top swcell_m20_v3_top -part $swc(part) -flatten_hierarchy none -generic [list STORAGE_MODE=$mode PONG_FILE=$pong SNAKE_FILE=$snake SNAKE_TICK_DONE=$snake_done]
 read_xdc $xdc
 create_clock -name sys_clk -period 20.0 [get_ports sys_clk]
 set_output_delay -clock sys_clk -max 5.0 [all_outputs]
 set_output_delay -clock sys_clk -min 0.0 [all_outputs]
 set first [get_pins -hier -quiet -regexp {.*filter/sync_inputs/pipe_reg\[0\].*/D}]
 set rx [get_pins -hier -quiet -regexp {.*rx_sync/pipe_reg\[0\].*/D}]
 if {[llength $first]!=9||[llength $rx]!=1} {error "Expected exactly 9+1 first synchronization registers"}
 set_false_path -from [get_ports {RST_N KEY0 KEY1 KEY2 KEY3 KEY4 KEY5 KEY6 KEY7}] -to $first
 set_false_path -from [get_ports UART_RXD] -to $rx
 # No false paths or unconstrained fabric clocks in CPU logic. Try ordinary 50MHz STA first.
 set muxes [get_cells -hier -filter {REF_NAME == LUT3 && NAME =~ *cpu*cell_mux}]
 set expected [expr {$mode eq "STRICT_MUX"?543:477}]
 if {[llength $muxes]!=$expected} {error "CPU mux mapping differs: [llength $muxes], expected $expected"}
 set f [open [file join $output cpu_mux_cells.txt] w];foreach cell $muxes {puts $f $cell};close $f
 report_utilization -hierarchical -file [file join $output synth_utilization.rpt]
 report_timing_summary -report_unconstrained -file [file join $output synth_timing.rpt]
 report_drc -checks [get_drc_checks LUTLP-1] -file [file join $output feedback_drc.rpt]
 if {$stage eq "synth"} {puts "M20_V3_SYNTH_COMPLETE mode=$mode muxes=[llength $muxes]";return}
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
 if {[llength $violations]} {error "DRC_BLOCKED_$mode: [llength $violations] violations; no bitstream; see drc.rpt"}
 if {$mode eq "STRICT_MUX"} {error "STRICT_MUX requires explicit feedback/timing review even if DRC empty; never auto-program"}
 foreach type {max min} {
  set p [get_timing_paths -delay_type $type -max_paths 1]
  if {[llength $p]!=1||[get_property SLACK $p]<0} {error "FPGA_TIMING_FAILED_$type; no bitstream"}
 }
 # Retain explicit check_timing evidence; clocked native storage is all in sys_clk.
 check_timing -verbose -file [file join $output check_timing.rpt]
 dict for {file digest} $hashes {if {[lindex [exec sha256sum $file] 0] ne $digest} {error "SOURCE_CHANGED_DURING_BUILD $file"}}
 set_property BITSTREAM.STARTUP.STARTUPCLK JTAGCLK [current_design]
 set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]
 write_bitstream [file join $output swcell_m20_v3_top.bit]
 puts "M20_V3_BITSTREAM_PASS $output/swcell_m20_v3_top.bit"
}
if {[catch {main} message]} {puts stderr "M20_V3_BUILD_ERROR: $message";exit 1}
exit 0
