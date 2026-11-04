# M11 functional test parameters; shared hardware values are owned by the board profile.
source [file join [file dirname [info script]] ../../../../boards/swcell_k325t/board.tcl]
set swc(board_xdc) [file normalize [file join [file dirname [info script]] ../../../../boards/swcell_k325t/constraints/base_io.xdc]]
set swc(module_xdc) [file normalize [file join [file dirname [info script]] ../../common/constraints/m11_io.xdc]]
set swc(por_ms) 100
set swc(uart_baud) 115200
set swc(step_ns) 500
set swc(settle_ns) 200
set swc(sync_stages) 2
set swc(pattern_steps) 32
set swc(random_steps) 1024
