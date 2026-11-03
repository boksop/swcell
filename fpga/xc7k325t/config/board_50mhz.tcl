# User-provided hardware: XC7K325T-2FFG900C, all listed IO 3.3 V single-ended.
# Commercial temperature grade C is recorded here; Vivado part excludes trailing C.
set swc(part) xc7k325tffg900-2
set swc(clk_hz) 50000000
set swc(board_xdc) ../constraints/board_50mhz.xdc
set swc(por_ms) 100
set swc(uart_baud) 115200
set swc(step_ns) 500
set swc(settle_ns) 200
set swc(sync_stages) 2
set swc(pattern_steps) 32
set swc(random_steps) 1024
set swc(flash_model) N25Q256A13EF840F
# Master SPI mode straps are M[2:0]=001; x4 is selected by the bitstream.
set swc(flash_enable) 1
set swc(boot_mode_bits) 001
set swc(flash_cfgmem_part) mt25ql256-spi-x1_x2_x4
set swc(flash_cfgmem_alias) n25q256-3.3v-spi-x1_x2_x4
set swc(flash_size_mib) 32
set swc(flash_buswidth) 4
set swc(flash_transfer) SDR
set swc(flash_fall_edge) 1
set swc(flash_32bit_addr) 1
set swc(flash_compress) 1
set swc(configrate_mhz) auto
# Timing inputs: Micron STR clock-to-out at <=30 pF and XC7K325T SPI setup.
set swc(flash_tco_ns) 7.0
set swc(fpga_spi_setup_ns) 3.0
set swc(cclk_tolerance) 0.5
set swc(flash_sdr_max_mhz) 108.0
set swc(fpga_cclk_max_mhz) 100.0
# Explicit ENGINEERING BUDGET, NOT a measured board propagation delay.
# Measure CCLK outward + worst DQ return propagation/loading before speed sign-off.
set swc(flash_board_delay_budget_ns) 2.0
