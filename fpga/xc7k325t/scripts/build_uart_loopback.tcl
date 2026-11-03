proc run {} {
 set root [file normalize [file join [file dirname [info script]] ../../..]]
 set out [file join $root build uart_loopback]
 file mkdir $out
 create_project -in_memory -part xc7k325tffg900-2
 read_verilog -sv [file join $root rtl common swc_input_sync.sv]
 read_verilog -sv [file join $root fpga xc7k325t diagnostics swcell_uart_loopback_top.sv]
 synth_design -top swcell_uart_loopback_top -part xc7k325tffg900-2
 read_xdc [file join $root fpga xc7k325t constraints board_50mhz.xdc]
 create_clock -name sys_clk -period 20.0 [get_ports sys_clk]
 set_property BITSTREAM.STARTUP.STARTUPCLK JTAGCLK [current_design]
 set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]
 opt_design
 place_design
 route_design
 # Persist evidence for checking physical pins and the direct RX-to-TX path.
 foreach {port expected direction} {UART_RXD V20 IN UART_TX W23 OUT} {
   if {[get_property PACKAGE_PIN [get_ports $port]] ne $expected} {
     error "Unexpected physical pin for $port"
   }
   if {[get_property DIRECTION [get_ports $port]] ne $direction} {
     error "Unexpected direction for $port"
   }
 }
 set rx_net [get_nets -of_objects [get_pins UART_RXD_IBUF_inst/O]]
 set tx_net [get_nets -of_objects [get_pins UART_TX_OBUF_inst/I]]
 if {[llength $rx_net] != 1 || $rx_net ne $tx_net} {
   error "UART RX IBUF must directly drive TX OBUF"
 }
 report_io -file [file join $out io.rpt]
 set evidence [open [file join $out connectivity.rpt] w]
 puts $evidence "UART_RXD V20 IN -> IBUF -> $rx_net -> OBUF -> UART_TX W23 OUT"
 puts $evidence "UART_DIRECT_LOOPBACK_CONNECTIVITY_PASS"
 close $evidence
 write_checkpoint -force [file join $out routed.dcp]
 report_timing_summary -file [file join $out timing.rpt]
 report_drc -file [file join $out drc.rpt]
 if {[llength [get_drc_violations -quiet]]} {error "Loopback diagnostic DRC failed"}
 write_bitstream -force [file join $out swcell_uart_loopback_top.bit]
 puts "UART_LOOPBACK_BUILD_PASS"
}
if {[catch {run} message]} {puts stderr "UART_LOOPBACK_BUILD_ERROR $message";exit 1}
exit 0
