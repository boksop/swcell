#!/usr/bin/env bash
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
P="${SWCELL_PYTHON:-$R/build/venvs/python312/bin/python}"
V="${M20_VIVADO_BIN:-$HOME/AMDDesignTools/2026.1.1/Vivado/bin}"
D="${M20V31_OUTPUT:-$R/build/sim/m20_v31/joint_$(date +%Y%m%d_%H%M%S)}"
[[ ! -e "$D" ]] || { echo 'Use a fresh output directory';exit 1; }
export PYTHONDONTWRITEBYTECODE=1
"$P" -B "$R/tools/m20/v31/verify_firmware.py" --output "$D" --vectors
D="$(cd "$D" && pwd)"
"$P" -B "$R/tools/m20/v31/build_firmware.py" --output "$D/firmware"
cmp "$D/firmware/m20_v31.memh" "$R/software/m20_300/v31/m20_v31.memh"
mkdir "$D/xsim";cd "$D/xsim"
sources=()
for n in swc_input_sync swc_power_on_reset swc_debounce swc_uart_tx swc_uart_rx swc_uart_hex_json;do sources+=("$R/rtl/common/$n.sv");done
for n in m20_pkg m20_alu m20_decoder m20_control m20_pc m20_ar m20_cpu_core;do sources+=("$R/rtl/m20/$n.sv");done
sources+=("$R/rtl/modules/m20/v3/swc_v3_mux157.sv" "$R/rtl/modules/m20/v3/generated/m20v3_cpu_core.sv")
for n in swc_m20_v31_gpio swc_m20_v31_memory swc_m20_v31_service;do sources+=("$R/rtl/modules/m20/v31/$n.sv");done
sources+=("$R/fpga/projects/m20/autonomous/rtl/swcell_m20_v31_top.sv" "$R/sim/m20_v31/ssd1306_cpu_model.sv" "$R/sim/m20_v31/tb_m20_v31_joint.sv")
"$V/xvlog" --sv "${sources[@]}" > compile.log 2>&1
"$V/xelab" tb_m20_v31_joint -s joint --timescale 1ns/1ps --generic_top "ROM_FILE=$D/firmware/m20_v31.memh" > elaborate.log 2>&1
"$V/xsim" joint --tclbatch "$R/sim/oled_keys/run.tcl" --testplusarg "OUT=$D" --log simulation.log > console.log 2>&1
grep 'M20_V31_JOINT_PASS' simulation.log
! grep -q 'Fatal:' simulation.log

"$P" -B "$R/host/python/swcell_m20_v31.py" --input "$D/uart.jsonl" --output "$D/parsed_uart"
