# Local read-only inspection of an existing routed checkpoint.
# vivado -mode batch -source tools/m20/v3_route_audit.tcl -tclargs DCP FRESH_OUTPUT
if {[llength $argv]!=2} {error "DCP FRESH_OUTPUT required"}
lassign $argv dcp output
if {[file exists $output]} {error "Choose fresh audit output"}
file mkdir $output
open_checkpoint $dcp
set muxes [get_cells -hier -filter {REF_NAME == LUT3 && NAME =~ *cpu*cell_mux}]
set f [open [file join $output mux_mapping.csv] w]
puts $f "instance,reference,init,site,bel,input_i0,input_i1,select"
foreach cell $muxes {
 set values [list $cell [get_property REF_NAME $cell] [get_property INIT $cell] [get_property LOC $cell] [get_property BEL $cell]]
 foreach pin {I0 I1 I2} {lappend values [get_nets -of_objects [get_pins $cell/$pin]]}
 puts $f [join $values ,]
}
close $f
set ff [get_cells -hier -filter {NAME =~ *system/cpu/* && REF_NAME =~ FD*}]
set clocks [get_cells -hier -filter {REF_NAME =~ BUFG*}]
set f [open [file join $output cpu_storage_ff.txt] w];foreach cell $ff {puts $f $cell};close $f
set f [open [file join $output counts.json] w]
puts $f "{\"mux_lut3\":[llength $muxes],\"cpu_native_ff\":[llength $ff],\"global_clock_buffers\":[llength $clocks]}";close $f
report_clock_utilization -file [file join $output clocks.rpt]
puts "M20_V3_ROUTED_MAPPING muxes=[llength $muxes] ff=[llength $ff]"
close_design
exit 0
