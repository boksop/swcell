open_vcd penetration.vcd
log_vcd [get_objects -r /tb_m20v23_penetration/*]
run all
close_vcd
quit
