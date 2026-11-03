# Independent JTAG-only diagnostic: BOTH V20 and W23 actively transmit.
proc run {} {
 set root [file normalize [file join [file dirname [info script]] ../../..]]
 set out [file join $root build uart_pin_id]
 file mkdir $out
 create_project -in_memory -part xc7k325tffg900-2
 foreach name {swc_power_on_reset swc_uart_tx swc_uart_text_beacon} {
   read_verilog -sv [file join $root rtl common ${name}.sv]
 }
 read_verilog -sv [file join $root fpga xc7k325t diagnostics swcell_uart_pin_id_top.sv]
 synth_design -top swcell_uart_pin_id_top -part xc7k325tffg900-2
 read_xdc [file join $root fpga xc7k325t constraints uart_pin_id.xdc]
 set_property BITSTREAM.STARTUP.STARTUPCLK JTAGCLK [current_design]
 set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]
 opt_design
 place_design
 route_design
 foreach {name pin} {PIN_V20_TX V20 PIN_W23_TX W23} {
   if {[get_property PACKAGE_PIN [get_ports $name]] ne $pin ||
       [get_property DIRECTION [get_ports $name]] ne "OUT"} {
     error "Diagnostic requires $name to be OUTPUT at $pin"
   }
 }
 report_io -file [file join $out io.rpt]
 report_timing_summary -file [file join $out timing.rpt]
 set setup [get_timing_paths -quiet -delay_type max -max_paths 1]
 set hold [get_timing_paths -quiet -delay_type min -max_paths 1]
 foreach path [concat $setup $hold] {
   if {[get_property SLACK $path]<0} {error "Pin-ID diagnostic timing failed"}
 }
 report_drc -file [file join $out drc.rpt]
 if {[llength [get_drc_violations -quiet]]} {error "Pin-ID diagnostic DRC failed"}
 write_checkpoint -force [file join $out routed.dcp]
 write_bitstream -force [file join $out swcell_uart_pin_id_top.bit]
 puts "UART_PIN_ID_BUILD_PASS V20=OUT W23=OUT BAUD=115200"
}
if {[catch {run} message]} {puts stderr "UART_PIN_ID_BUILD_ERROR $message";exit 1}
exit 0
