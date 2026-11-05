# Read-only routed design inspection; no clock or loop waivers.
if {[llength $argv]!=2} {error "ROUTED_DCP FRESH_OUTPUT required"}
lassign $argv dcp output
if {[file exists $output]} {error "Use fresh audit output"}
file mkdir $output
open_checkpoint $dcp
set muxes [get_cells -hier -filter {REF_NAME == LUT3 && NAME =~ *cpu*cell_mux}]
set ff [get_cells -hier -filter {NAME =~ *service/cpu/* && REF_NAME =~ FD*}]
set bufg [get_cells -hier -filter {REF_NAME =~ BUFG*}]
if {[llength $muxes]!=477||[llength $ff]!=33||[llength $bufg]!=1} {error "V31 CPU mapping changed"}
set f [open [file join $output mux_mapping.csv] w]
puts $f "instance,reference,init,site,bel,input_i0,input_i1,select"
foreach cell $muxes {
 set values [list $cell [get_property REF_NAME $cell] [get_property INIT $cell] [get_property LOC $cell] [get_property BEL $cell]]
 foreach pin {I0 I1 I2} {lappend values [get_nets -of_objects [get_pins $cell/$pin]]}
 puts $f [join $values ,]
};close $f
set f [open [file join $output oled_drivers.csv] w];puts $f "port,leaf_driver,reference"
foreach port {OLED_CS_N OLED_DC OLED_SCK OLED_MOSI} {
 set obuf [get_cells -of_objects [get_nets -of_objects [get_ports $port]] -filter {REF_NAME == OBUF}]
 if {[llength $obuf]!=1} {error "No unique output buffer $port"}
 set nets [get_nets -segments -of_objects [get_pins $obuf/I]]
 set drivers [get_pins -leaf -of_objects $nets -filter {DIRECTION == OUT}]
 if {[llength $drivers]!=1} {error "Non-unique CPU GPIO driver $port: $drivers"}
 set driver [lindex $drivers 0];set cell [get_cells -of_objects $driver]
 if {![string match "*service/cpu/*gpo*" $cell]||![string match FD* [get_property REF_NAME $cell]]} {
  error "OLED bypass detected $port driven by $driver"
 }
 puts $f "$port,$driver,[get_property REF_NAME $cell]"
};close $f
set f [open [file join $output counts.json] w]
puts $f "{\"mux_lut3\":477,\"cpu_native_ff\":33,\"global_clock_buffers\":1,\"oled_cpu_gpo_direct_drivers\":4,\"mode\":\"FUNCTIONAL_STORAGE\"}";close $f
report_clock_utilization -file [file join $output clocks.rpt]
puts "M20_V31_ROUTE_AUDIT_PASS muxes=477 ff=33 oled_direct=4"
close_design
exit 0
