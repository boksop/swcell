#!/usr/bin/env bash
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
V="${M20_VIVADO_BIN:-$HOME/AMDDesignTools/2026.1.1/Vivado/bin}"
D="${M20V3_INPUT_OUTPUT:-$R/build/sim/m20_v3/inputs_$(date +%Y%m%d_%H%M%S)}"
[[ ! -e "$D" ]] || exit 1
mkdir -p "$D";cd "$D"
"$V/xvlog" --sv "$R/rtl/common/swc_key_event_buffer.sv" "$R/sim/m20_v3/tb_key_event_buffer.sv" > compile.log 2>&1
"$V/xelab" tb_key_event_buffer -s keys --timescale 1ns/1ps > elaborate.log 2>&1
"$V/xsim" keys --tclbatch "$R/sim/oled_keys/run.tcl" --log simulation.log > console.log 2>&1
grep 'M20_V3_KEY_BUFFER_PASS' simulation.log
! grep -q 'Fatal:' simulation.log
