# Vivado 2022.1: vivado -mode batch -source .../build.tcl -tclargs --config ... --stage synth
proc swc_main {} {
    global argv swc
    source [file join [file dirname [info script]] ../../../../common/tcl/repo_paths.tcl]
    set root [swc_repo_root [info script]]
    # info script inside a proc remains the active sourced script.
    array set swc {part {} clk_hz {} board_xdc {} module_xdc {} uart_baud 115200 step_ns 500 settle_ns 200 sync_stages 2 pattern_steps 32 random_steps 1024 por_ms 100}
    set config [file join $root fpga projects m11 functional config board.local.tcl]
    if {![file isfile $config]} {set config [file join $root fpga projects m11 functional config default.tcl]}
    if {[info exists ::env(SWCELL_BOARD_CONFIG)]} {set config $::env(SWCELL_BOARD_CONFIG)}
    set stage create
    for {set i 0} {$i < [llength $argv]} {incr i} {
        set arg [lindex $argv $i]
        if {$arg ni {--config --stage} || $i+1 >= [llength $argv]} {error "Usage: --config BOARD.tcl --stage create|synth|bitstream"}
        incr i
        if {$arg eq "--config"} {set config [lindex $argv $i]} else {set stage [lindex $argv $i]}
    }
    if {$stage ni {create synth bitstream}} {error "Invalid stage: $stage"}
    if {![file isfile $config]} {error "Missing board config: $config. Copy board.example.tcl and supply exact part and clock frequency; see README.md."}
    set config [file normalize $config]
    source $config
    source [file join $root fpga common tcl flash_config.tcl]
    set flash [swc_flash_settings swc]
    if {$swc(part) eq "" || ![regexp {^xc7k325t[a-zA-Z0-9-]+$} $swc(part)]} {
        error "swc(part) must be the EXACT complete XC7K325T package/speed part; no guessed default is used."
    }
    set parts [get_parts -quiet $swc(part)]
    if {[llength $parts] != 1 || [get_property NAME $parts] ne $swc(part)} {error "Unknown or ambiguous FPGA part: $swc(part)"}
    foreach key {clk_hz uart_baud step_ns settle_ns sync_stages pattern_steps random_steps por_ms} {
        if {![string is integer -strict $swc($key)] || $swc($key)<=0} {error "swc($key) must be a positive integer"}
    }
    set step_cycles [expr {wide($swc(clk_hz))*$swc(step_ns)+999999999}]
    set step_cycles [expr {$step_cycles/1000000000}]
    set settle_cycles [expr {(wide($swc(clk_hz))*$swc(settle_ns)+999999999)/1000000000}]
    set por_cycles [expr {(wide($swc(clk_hz))*$swc(por_ms)+999)/1000}]
    if {$por_cycles>2147483647} {error "POR duration exceeds the supported 31-bit cycle count"}
    set uart_div [expr {($swc(clk_hz)+$swc(uart_baud)/2)/$swc(uart_baud)}]
    if {$swc(step_ns)<500 || $swc(settle_ns)<200 || $swc(sync_stages)<2 ||
        $step_cycles<$settle_cycles+$swc(sync_stages)+2 || $uart_div<2 || $swc(pattern_steps)<8} {
        error "Invalid timing/iteration configuration: need >=500ns steps, >=200ns settle plus CDC margin, >=8 pattern bits."
    }
    set baud_error [expr {abs(double($swc(clk_hz))/$uart_div/$swc(uart_baud)-1.0)}]
    if {$baud_error>0.02} {error "UART rounded divider error exceeds 2%; choose a compatible baud rate."}
    foreach key {board_xdc module_xdc} {
        if {$swc($key) ne ""} {
            if {[file pathtype $swc($key)] eq "relative"} {set swc($key) [file join [file dirname $config] $swc($key)]}
            if {![file isfile $swc($key)]} {error "Constraint file does not exist: $swc($key)"}
        }
    }
    if {$stage eq "bitstream" && $swc(board_xdc) eq ""} {error "Bitstream requires a real board_xdc; the template is intentionally incomplete."}
    set out [file join $root build fpga m11 functional]
    create_project -force swcell_m11 $out -part $swc(part)
    set_property target_language Verilog [current_project]
    set sources [concat [glob [file join $root rtl common *.sv]] [glob [file join $root rtl modules m11 *.sv]] [glob [file join $root fpga projects m11 functional rtl *.sv]]]
    add_files -norecurse $sources
    set_property top swcell_fpga_top [current_fileset]
    set generics [list CLK_HZ=$swc(clk_hz) POR_CYCLES=$por_cycles UART_BAUD=$swc(uart_baud) STEP_NS=$swc(step_ns) SETTLE_NS=$swc(settle_ns) SYNC_STAGES=$swc(sync_stages) PATTERN_STEPS=$swc(pattern_steps) RANDOM_STEPS=$swc(random_steps)]
    set_property generic [join $generics " "] [current_fileset]
    set clock_xdc [file join $out clock.xdc]
    set handle [open $clock_xdc w]
    puts $handle "create_clock -name sys_clk -period [format %.6f [expr {1.0e9/$swc(clk_hz)}]] \[get_ports sys_clk\]"
    close $handle
    add_files -fileset constrs_1 $clock_xdc
    if {[dict get $flash enabled]} {
        set flash_xdc [file join $out flash_config.xdc]
        swc_flash_write_xdc $flash $flash_xdc
        add_files -fileset constrs_1 $flash_xdc
        puts "SWCELL_FLASH_CONFIG: $flash"
    }
    add_files -fileset constrs_1 [file join $root fpga projects m11 functional constraints cdc.xdc]
    foreach key {board_xdc module_xdc} {if {$swc($key) ne ""} {add_files -fileset constrs_1 [file normalize $swc($key)]}}
    add_files -fileset sim_1 [glob [file join $root sim models *.sv]]
    add_files -fileset sim_1 [glob [file join $root sim m11 *.sv]]
    set_property top tb_m11 [get_filesets sim_1]
    update_compile_order -fileset sources_1
    if {$stage eq "create"} {puts "SWCELL_CREATE_PASS: $out/swcell_m11.xpr";return}
    launch_runs synth_1 -jobs 4
    wait_on_run synth_1
    if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {error "Synthesis failed; inspect build/fpga/m11/functional/swcell_m11.runs/synth_1/runme.log"}
    open_run synth_1
    set sync_d [get_pins -hier -quiet -regexp {.*inputs_sync/pipe_reg\[0\].*/D}]
    if {[llength $sync_d] != 3} {error "Expected 3 first-stage DUT synchronizer D pins; found [llength $sync_d]. Review cdc.xdc."}
    report_utilization -file [file join $out utilization.rpt]
    report_timing_summary -file [file join $out synth_timing.rpt]
    if {$stage eq "synth"} {puts "SWCELL_SYNTH_PASS";return}
    # Explicit preflight: never lower UCIO/NSTD DRC severities.
    foreach port [get_ports] {
        foreach property {PACKAGE_PIN IOSTANDARD} {
            set value [get_property $property $port]
            if {$value eq "" || $value eq "DEFAULT"} {error "Unconfigured port $port: missing $property"}
        }
    }
    close_design
    launch_runs impl_1 -to_step write_bitstream -jobs 4
    wait_on_run impl_1
    if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "Implementation/bitstream failed; inspect implementation logs"}
    open_run impl_1
    report_timing_summary -file [file join $out timing.rpt]
    report_drc -file [file join $out drc.rpt]
    set worst [get_timing_paths -quiet -delay_type max -max_paths 1]
    if {[llength $worst] && [get_property SLACK $worst]<0} {error "Timing failed: do not program this bitstream"}
    set hold_path [get_timing_paths -quiet -delay_type min -max_paths 1]
    if {[llength $hold_path] && [get_property SLACK $hold_path]<0} {error "Hold timing failed"}
    set violations [get_drc_violations -quiet]
    if {[llength $violations]} {error "Unresolved design DRC violations: $violations; inspect drc.rpt"}
    if {[dict get $flash enabled]} {
        swc_flash_write_images $flash [file join $out swcell_m11.runs impl_1 swcell_fpga_top.bit] [file join $out flash]
    }
    puts "SWCELL_BITSTREAM_PASS: [file join $out swcell_m11.runs impl_1 swcell_fpga_top.bit]"
}
if {[catch {swc_main} message options]} {
    puts stderr "SWCELL_BUILD_ERROR: $message"
    exit 1
}
exit 0
