# This script ERASES/PROGRAMS the image range only when explicitly executed.
# Usage: program_flash.tcl IMAGE.mcs EXACT_DEVICE_NAME [BOARD_CONFIG] [EXACT_TARGET_NAME]
proc swc_program_flash {} {
    global argv swc
    source [file join [file dirname [info script]] repo_paths.tcl]
    set root [swc_repo_root [info script]]
    if {[llength $argv]<2 || [llength $argv]>4} {
        error "Usage: program_flash.tcl IMAGE.mcs EXACT_DEVICE_NAME ?BOARD_CONFIG? ?EXACT_TARGET_NAME?"
    }
    lassign $argv image device_name config target_name
    set image [file normalize $image]
    if {![file isfile $image] || [string tolower [file extension $image]] ne ".mcs"} {error "An existing generated MCS file is required"}
    if {$config eq ""} {set config [file join $root fpga boards swcell_k325t board.tcl]}
    source $config
    source [file join $root fpga common tcl flash_config.tcl]
    set settings [swc_flash_settings swc]
    if {![dict get $settings enabled]} {error "Flash programming profile is disabled"}
    set binary [file rootname $image].bin
    # Validate the paired generated image BEFORE connecting to any hardware.
    set python python3
    if {[file executable [file join $root .venv bin python]]} {set python [file join $root .venv bin python]}
    puts [exec $python [file join $root host python swcell_check_flash_image.py]         --mcs $image --bin $binary --size-mib [dict get $settings size_mib]]
    open_hw_manager
    connect_hw_server
    if {$target_name eq ""} {
        set targets [get_hw_targets]
        if {[llength $targets]!=1} {error "Multiple/no JTAG targets: supply an exact target name"}
        current_hw_target [lindex $targets 0]
    } else {
        set targets {}
        foreach t [get_hw_targets] {if {[get_property NAME $t] eq $target_name} {lappend targets $t}}
        if {[llength $targets]!=1} {error "Exact JTAG target not found: $target_name"}
        current_hw_target [lindex $targets 0]
    }
    open_hw_target
    set matches {}
    foreach d [get_hw_devices] {if {[get_property NAME $d] eq $device_name} {lappend matches $d}}
    if {[llength $matches]!=1} {error "Expected one exact device '$device_name'; available: [get_hw_devices]"}
    set device [lindex $matches 0]
    if {![string match xc7k325t* [get_property PART $device]]} {error "Selected device is not XC7K325T"}
    current_hw_device $device
    refresh_hw_device $device
    set memories [get_cfgmem_parts -quiet [dict get $settings cfgmem_part]]
    if {![llength $memories]} {error "Installed Vivado does not support the configured cfgmem part"}
    # Vivado returns duplicate catalog names for compatible FPGA families; the
    # first canonical object is the documented XAPP586 selection method.
    set mem [lindex $memories 0]
    if {[get_property NAME $mem] ne [dict get $settings cfgmem_part] ||
        [get_property MEM_DEVICE_ALIAS $mem] ne [dict get $settings cfgmem_alias] ||
        [get_property MEM_DENSITY $mem]!=8*[dict get $settings size_mib]} {
        error "Configuration-memory identity/voltage alias/capacity mismatch"
    }
    set hwmem [create_hw_cfgmem -hw_device $device -mem_dev $mem]
    set_property PROGRAM.ADDRESS_RANGE use_file $hwmem
    set_property PROGRAM.FILES [list $image] $hwmem
    set_property PROGRAM.UNUSED_PIN_TERMINATION pull-none $hwmem
    set_property PROGRAM.BLANK_CHECK 0 $hwmem
    set_property PROGRAM.ERASE 1 $hwmem
    set_property PROGRAM.CFG_PROGRAM 1 $hwmem
    set_property PROGRAM.VERIFY 1 $hwmem
    set access_bitfile [get_property PROGRAM.HW_CFGMEM_BITFILE $device]
    create_hw_bitstream -hw_device $device $access_bitfile
    set_property PROGRAM.FILE $access_bitfile $device
    program_hw_devices $device
    refresh_hw_device $device
    program_hw_cfgmem -hw_cfgmem $hwmem
    close_hw_manager
    puts "SWCELL_FLASH_PROGRAM_PASS (erase/program/verify complete; power cycle to test autonomous boot)"
}
if {[catch {swc_program_flash} message options]} {
    catch {close_hw_manager}
    puts stderr "SWCELL_FLASH_PROGRAM_ERROR: $message"
    exit 1
}
exit 0
