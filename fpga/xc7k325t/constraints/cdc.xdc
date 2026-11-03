# Only asynchronous input -> FIRST synchronizer stage is a false path.
# The remaining stages retain normal timing analysis and ASYNC_REG placement.
set swc_sync_d [get_pins -hier -quiet -regexp {.*inputs_sync/pipe_reg\[0\].*/D}]
# build.tcl checks that exactly three first-stage D pins survive synthesis.
set_false_path -from [get_ports {M11_DL_Q M11_DFF_Q M11_DFF_QM}] -to $swc_sync_d
# Internal POR deasserts synchronously; there is no external reset port.
