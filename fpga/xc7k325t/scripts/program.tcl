# Explicit device selection; no automatic first-device programming.
# vivado -mode batch -source program.tcl -tclargs BITFILE EXACT_DEVICE_NAME
proc swc_program {} {
    global argv
    if {[llength $argv]!=2} {error "Usage: program.tcl BITFILE EXACT_DEVICE_NAME (from Hardware Manager)"}
    lassign $argv bitfile device_name
    if {![file isfile $bitfile]} {error "Missing bitstream: $bitfile"}
    open_hw_manager
    connect_hw_server
    open_hw_target
    set selected {}
    foreach d [get_hw_devices] {if {[get_property NAME $d] eq $device_name} {lappend selected $d}}
    if {[llength $selected]!=1} {error "Expected one exact device '$device_name'; available: [get_hw_devices]"}
    set d [lindex $selected 0]
    if {![string match xc7k325t* [get_property PART $d]]} {error "Selected hardware is not XC7K325T"}
    current_hw_device $d
    refresh_hw_device $d
    set_property PROGRAM.FILE [file normalize $bitfile] $d
    program_hw_devices $d
    close_hw_manager
}
if {[catch {swc_program} message]} {puts stderr "SWCELL_PROGRAM_ERROR: $message";exit 1}
exit 0
