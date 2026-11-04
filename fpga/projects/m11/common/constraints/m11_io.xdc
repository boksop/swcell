# M11 daughtercard wiring verified in Phase1; combine with board base_io.xdc.
set_property PACKAGE_PIN L12 [get_ports M11_DL_D]
set_property PACKAGE_PIN F16 [get_ports M11_DL_EN]
set_property PACKAGE_PIN E15 [get_ports M11_DL_Q]
set_property PACKAGE_PIN H12 [get_ports M11_DFF_D]
set_property PACKAGE_PIN L11 [get_ports M11_DFF_CLK]
set_property PACKAGE_PIN J11 [get_ports M11_DFF_Q]
set_property PACKAGE_PIN E11 [get_ports M11_DFF_QM]
set_property IOSTANDARD LVCMOS33 [get_ports {M11_DL_D M11_DL_EN M11_DL_Q M11_DFF_D M11_DFF_CLK M11_DFF_Q M11_DFF_QM}]
