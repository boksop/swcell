# Copy to board.local.tcl (gitignored). Values must come from board schematics.
# No default part / board clock is selected by build.tcl.
set swc(part) ""             ;# TODO exact full XC7K325T package/speed part
set swc(clk_hz) ""           ;# TODO actual single-ended oscillator frequency (Hz)
set swc(board_xdc) ""        ;# TODO absolute path or path relative to THIS config
set swc(por_ms) 100        ;# FPGA configuration startup reset, no external pin
set swc(uart_baud) 115200
set swc(step_ns) 500
set swc(settle_ns) 200
set swc(sync_stages) 2
set swc(pattern_steps) 32
set swc(random_steps) 1024
# TODO if the board oscillator is differential, adapt the clock input wrapper
# with IBUFDS and the matching XDC before using this single-ended top.

# Enable only after supplying the complete Flash profile; see board_50mhz.tcl.
set swc(flash_enable) 0
