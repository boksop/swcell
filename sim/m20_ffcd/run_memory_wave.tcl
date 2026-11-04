open_vcd memory_service.vcd
log_vcd /tb_m20ffcd_memory/sys_clk /tb_m20ffcd_memory/clk_ref
log_vcd /tb_m20ffcd_memory/master_hold /tb_m20ffcd_memory/slave_open /tb_m20ffcd_memory/safe_hold
log_vcd /tb_m20ffcd_memory/ram_sample_ce /tb_m20ffcd_memory/write_ce /tb_m20ffcd_memory/rom_read_ce /tb_m20ffcd_memory/commit_ce /tb_m20ffcd_memory/observe_ce
log_vcd /tb_m20ffcd_memory/dut/state_q /tb_m20ffcd_memory/dut/state_qm /tb_m20ffcd_memory/dut/state_me /tb_m20ffcd_memory/dut/state_se
run all
close_vcd
quit
