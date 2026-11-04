#!/usr/bin/env bash
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
V="${M20_VIVADO_BIN:-$HOME/AMDDesignTools/2026.1.1/Vivado/bin}"
P="${SWCELL_PYTHON:-$R/build/venvs/python312/bin/python}"
D="${M20_FF16_REVIEW_OUTPUT_DIR:-$R/build/m20_300/v24_ff16/cones_replay_$(date +%Y%m%d_%H%M%S)}"
export PYTHONDONTWRITEBYTECODE=1
"$P" -B "$R/tools/m20/ff16_cones_replay.py" prepare --output "$D"
D="$(cd "$D" && pwd)"
mkdir "$D/xsim"
cd "$D/xsim"
"$V/xvlog" --sv "$R/sim/m20_ff16/swc_ff16_timing.sv" "$D/frozen_cone.sv" "$R/sim/m20_ff16_review/tb_ff16_cpu_cones.sv" > compile.log 2>&1
"$V/xelab" tb_ff16_cpu_cones -s cones --debug all --timescale 1ns/1ps > elaborate.log 2>&1
"$V/xsim" cones --tclbatch "$R/sim/m20_ff16_review/run_cones.tcl" --testplusarg "REVIEW=$D" --log cones.log > console.log 2>&1
grep -q 'FF16_CPU_CONES_COMPLETE cases=632' cones.log
"$P" -B "$R/tools/m20/ff16_cones_replay.py" check --output "$D"
