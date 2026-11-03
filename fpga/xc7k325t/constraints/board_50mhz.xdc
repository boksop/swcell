# Pin map provided by the board owner. All listed IO use 3.3 V single-ended levels.
# build.tcl generates the 20 ns sys_clk constraint from the board configuration.
set_property PACKAGE_PIN D27 [get_ports sys_clk]
set_property PACKAGE_PIN R24 [get_ports LED_G]
set_property PACKAGE_PIN T20 [get_ports LED_Y]
set_property PACKAGE_PIN T21 [get_ports LED_R]
set_property PACKAGE_PIN W23 [get_ports UART_TX]
set_property PACKAGE_PIN V20 [get_ports UART_RXD]
set_property PACKAGE_PIN L12 [get_ports M11_DL_D]
set_property PACKAGE_PIN F16 [get_ports M11_DL_EN]
set_property PACKAGE_PIN E15 [get_ports M11_DL_Q]
set_property PACKAGE_PIN H12 [get_ports M11_DFF_D]
set_property PACKAGE_PIN L11 [get_ports M11_DFF_CLK]
set_property PACKAGE_PIN J11 [get_ports M11_DFF_Q]
set_property PACKAGE_PIN E11 [get_ports M11_DFF_QM]
set_property IOSTANDARD LVCMOS33 [get_ports {sys_clk LED_G LED_Y LED_R UART_TX UART_RXD M11_DL_D M11_DL_EN M11_DL_Q M11_DFF_D M11_DFF_CLK M11_DFF_Q M11_DFF_QM}]
# UART_RXD is reserved; not used as a reset or command input in Phase 1.
# No external reset port. Do not add CLOCK_DEDICATED_ROUTE FALSE workarounds.

# User-confirmed configuration-bank wiring: VCCO_0=3.3 V, CFGBVS tied to VCCO.
set_property CFGBVS VCCO [current_design]
set_property CONFIG_VOLTAGE 3.3 [current_design]
