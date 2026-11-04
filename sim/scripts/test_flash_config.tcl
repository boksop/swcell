# No Vivado or board required: tclsh8.6 sim/scripts/test_flash_config.tcl
set root [file normalize [file join [file dirname [info script]] ../..]]
source [file join $root fpga common tcl flash_config.tcl]
source [file join $root fpga boards swcell_k325t board.tcl]
proc require {condition message} {if {![uplevel 1 [list expr $condition]]} {error $message}}
set settings [swc_flash_settings swc]
require {[dict get $settings rate_mhz]==50} "Expected 50 MHz auto selection"
require {abs([dict get $settings worst_cclk_mhz]-75.0)<1e-9} "Oscillator tolerance missing"
require {[dict get $settings margin_ns]>1.3} "Insufficient budget margin"
set swc(configrate_mhz) 66
require {[catch {swc_flash_settings swc}]} "Unsafe 66 MHz must fail"
set swc(configrate_mhz) 33
require {[dict get [swc_flash_settings swc] rate_mhz]==33} "Manual lower speed must work"
set swc(configrate_mhz) auto
set swc(flash_board_delay_budget_ns) 4.0
require {[dict get [swc_flash_settings swc] rate_mhz]==40} "Longer board delay must lower rate"
set swc(flash_board_delay_budget_ns) 2.0
set swc(flash_fall_edge) 0
require {[dict get [swc_flash_settings swc] rate_mhz]==26} "Rising-edge sample needs half-period budget"
set swc(flash_fall_edge) 1
set swc(flash_transfer) DTR
require {[catch {swc_flash_settings swc}]} "DTR request must fail rather than silently map to SDR"
set swc(flash_transfer) SDR
set swc(flash_32bit_addr) 0
require {[catch {swc_flash_settings swc}]} "256-Mbit Flash requires 32-bit address setting"
puts "FLASH_CONFIG_TEST_PASS rate=50 worst_case=75MHz margin=1.333ns"
