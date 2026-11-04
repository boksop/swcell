#!/usr/bin/env bash
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
V="${M20_VIVADO_BIN:-$HOME/AMDDesignTools/2026.1.1/Vivado/bin}"
D="${M20V3_SYSTEM_OUTPUT:-$R/build/sim/m20_v3/system_$(date +%Y%m%d_%H%M%S)}"
[[ ! -e "$D" ]] || { echo 'Use fresh V3 system output';exit 1; }
mkdir -p "$D";D="$(cd "$D" && pwd)";cd "$D"
"$V/xvlog" --sv "$R/rtl/modules/m20/v3/generated/m20_v3_game_pkg.sv" \
 "$R/rtl/modules/m20/v3/swc_v3_mux157.sv" "$R/rtl/modules/m20/v3/generated/m20v3_cpu_core.sv" \
 "$R/rtl/modules/m20/v3/swc_m20_v3_memory.sv" "$R/rtl/modules/m20/v3/swc_m20_v3_system.sv" "$R/sim/m20_v3/tb_m20_v3_system.sv" > compile.log 2>&1
"$V/xelab" tb_m20_v3_system -s system --debug all --timescale 1ns/1ps \
 --generic_top "PONG_FILE=$R/rtl/modules/m20/v3/generated/pong.memh" \
 --generic_top "SNAKE_FILE=$R/rtl/modules/m20/v3/generated/snake.memh" > elaborate.log 2>&1
"$V/xsim" system --tclbatch "$R/sim/oled_keys/run.tcl" --testplusarg "OUT=$D" --log simulation.log > console.log 2>&1
grep 'M20_V3_SYSTEM_PASS' simulation.log
! grep -q 'Fatal:' simulation.log
"${SWCELL_PYTHON:-$R/build/venvs/python312/bin/python}" -B "$R/tools/m20/v3_verify_frames.py" "$D/frame_snapshots.csv"
