#!/usr/bin/env bash
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
V="${M20_VIVADO_BIN:-$HOME/AMDDesignTools/2026.1.1/Vivado/bin}"
SNAKE_FILE="${M20V3_BOARD_SNAKE_FILE:-$R/rtl/modules/m20/v3/generated/snake.memh}"
SNAKE_DONE="${M20V3_BOARD_SNAKE_DONE:-316}"
D="${M20V3_BOARD_OUTPUT:-$R/build/sim/m20_v3/board_$(date +%Y%m%d_%H%M%S)}"
[[ ! -e "$D" ]] || { echo 'Use fresh V3 board output';exit 1; }
mkdir -p "$D";D="$(cd "$D" && pwd)";cd "$D"
sources=()
for n in swc_input_sync swc_power_on_reset swc_debounce swc_key_event_buffer swc_spi_tx swc_uart_tx swc_uart_rx swc_uart_hex_json;do sources+=("$R/rtl/common/$n.sv");done
sources+=("$R/rtl/common/display/swc_ssd1306.sv" "$R/fpga/projects/diagnostics/oled_keys/rtl/swc_oled_font_pkg.sv" "$R/rtl/modules/m20/v3/generated/m20_v3_game_pkg.sv" "$R/rtl/modules/m20/v3/swc_v3_mux157.sv" "$R/rtl/modules/m20/v3/generated/m20v3_cpu_core.sv")
for n in swc_m20_v3_memory swc_m20_v3_system swc_m20_v3_display;do sources+=("$R/rtl/modules/m20/v3/$n.sv");done
sources+=("$R/fpga/projects/m20/cpu_validation/rtl/swcell_m20_v3_top.sv" "$R/sim/oled_keys/ssd1306_spi_model.sv" "$R/sim/m20_v3/tb_m20_v3_board.sv")
"$V/xvlog" --sv "${sources[@]}" > compile.log 2>&1
"$V/xelab" tb_m20_v3_board -s board --debug all --timescale 1ns/1ps \
 --generic_top "PONG_FILE=$R/rtl/modules/m20/v3/generated/pong.memh" \
 --generic_top "SNAKE_FILE=$SNAKE_FILE" --generic_top "SNAKE_TICK_DONE=$SNAKE_DONE" > elaborate.log 2>&1
"$V/xsim" board --tclbatch "$R/sim/oled_keys/run.tcl" --testplusarg "OUT=$D" --log simulation.log > console.log 2>&1
grep 'M20_V3_BOARD_PASS' simulation.log
! grep -q 'Fatal:' simulation.log
"${SWCELL_PYTHON:-$R/build/venvs/python312/bin/python}" -B "$R/host/python/swcell_m20_v3.py" --input "$D/uart.jsonl" --output "$D/parsed"
