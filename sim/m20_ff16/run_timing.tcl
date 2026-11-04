open_vcd timing.vcd
foreach signal {clk_ref safe_hold data_drive h s cd tap4 tap8 tap12 tap16 q qm me se hl sl} {
 set objects [get_objects /*/u/$signal]
 if {[llength $objects]>0} {log_vcd $objects}
}
run all
close_vcd
quit
