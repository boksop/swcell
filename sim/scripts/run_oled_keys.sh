#!/usr/bin/env bash
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
V="${M20_VIVADO_BIN:-$HOME/AMDDesignTools/2026.1.1/Vivado/bin}"
P="${SWCELL_PYTHON:-$R/build/venvs/python312/bin/python}"
D="${SWCELL_IO_SIM_OUTPUT:-$R/build/sim/diagnostics/oled_keys/run_$(date +%Y%m%d_%H%M%S)}"
[[ ! -e "$D" ]] || { echo 'Choose fresh OLED simulation output';exit 1; }
mkdir -p "$D";D="$(cd "$D" && pwd)";cd "$D"
"$V/xvlog" --sv "$R/rtl/common/swc_input_sync.sv" "$R/rtl/common/swc_power_on_reset.sv" "$R/rtl/common/swc_debounce.sv" "$R/rtl/common/swc_spi_tx.sv" "$R/rtl/common/swc_uart_tx.sv" "$R/rtl/common/display/swc_ssd1306.sv" \
 "$R/fpga/projects/diagnostics/oled_keys/rtl/swc_oled_font_pkg.sv" "$R/fpga/projects/diagnostics/oled_keys/rtl/swc_io_diag_pixels.sv" "$R/fpga/projects/diagnostics/oled_keys/rtl/swc_io_diag_uart.sv" "$R/fpga/projects/diagnostics/oled_keys/rtl/swcell_oled_keys_top.sv" \
 "$R/sim/oled_keys/ssd1306_spi_model.sv" "$R/sim/oled_keys/tb_oled_keys.sv" "$R/sim/oled_keys/tb_oled_refresh.sv" > compile.log 2>&1
"$V/xelab" tb_oled_keys -s oled_keys --debug all --timescale 1ns/1ps > elaborate.log 2>&1
"$V/xsim" oled_keys --tclbatch "$R/sim/oled_keys/run.tcl" --testplusarg "OUT=$D" --log simulation.log > console.log 2>&1
grep 'OLED_KEYS_SIM_PASS' simulation.log
if grep -q 'Fatal:' simulation.log;then exit 1;fi
"$P" -B "$R/host/python/swcell_io_diag.py" --input "$D/uart.jsonl" --output "$D/parsed" --require-fpga-coverage
"$V/xelab" tb_oled_refresh -s oled_refresh --debug all --timescale 1ns/1ps > refresh_elaborate.log 2>&1
"$V/xsim" oled_refresh --tclbatch "$R/sim/oled_keys/run.tcl" --log refresh.log > refresh_console.log 2>&1
grep 'OLED_REFRESH_PASS' refresh.log
if grep -q 'Fatal:' refresh.log;then exit 1;fi
echo "OLED_KEYS_REGRESSION_PASS $D"
