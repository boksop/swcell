# TEMPLATE ONLY: there are deliberately NO fabricated package pins.
# Copy to board.local.xdc and fill every port from your board schematic.
# build.tcl creates sys_clk from swc(clk_hz); do not duplicate create_clock here.
# Example syntax (replace placeholders; commented lines have no effect):
# set_property PACKAGE_PIN <ACTUAL_PIN> [get_ports sys_clk]
# set_property IOSTANDARD <ACTUAL_CLOCK_STANDARD> [get_ports sys_clk]
# No external reset port: internal FPGA INIT-based power-on reset.
# TODO UART_TX: correct voltage / IOSTANDARD for the board's UART bridge.
# TODO M11_DL_D, M11_DL_EN, M11_DL_Q
# TODO M11_DFF_D, M11_DFF_CLK, M11_DFF_Q, M11_DFF_QM
# TODO LED_G, LED_Y, LED_R: active-high PASS / RUNNING / FAIL.
# TODO UART_RXD: reserved input; no command parser in Phase 1.
# Every top port needs both PACKAGE_PIN and IOSTANDARD for bitstream generation.
# All seven M11 signals require a bank whose VCCO supports 3.3 V LVCMOS33.
# set_property IOSTANDARD LVCMOS33 [get_ports {M11_DL_D M11_DL_EN M11_DL_Q M11_DFF_D M11_DFF_CLK M11_DFF_Q M11_DFF_QM}]
# TODO drive strength / slew / board loading from schematics, when appropriate.
# No generated clock is to be created on M11_DFF_CLK: it is a data output.
