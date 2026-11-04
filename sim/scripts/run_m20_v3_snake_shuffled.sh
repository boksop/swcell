#!/usr/bin/env bash
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
P="${SWCELL_PYTHON:-$R/build/venvs/python312/bin/python}"
V="${M20_VIVADO_BIN:-$HOME/AMDDesignTools/2026.1.1/Vivado/bin}"
D="${M20V3_SHUFFLED_OUTPUT:-$R/build/sim/m20_v3/shuffled_$(date +%Y%m%d_%H%M%S)}"
[[ ! -e "$D" ]] || exit 1
export PYTHONPATH="$R/host/python" PYTHONDONTWRITEBYTECODE=1
"$P" "$R/tools/m20/v3_snake_shuffled_verify.py" --output "$D"
D="$(cd "$D" && pwd)";mkdir "$D/tb" "$D/xsim"
"$P" - "$R" "$D" <<'PY'
from pathlib import Path
import sys
r,d=map(Path,sys.argv[1:])
s=(r/'sim/m20_v21/m20v21_tb_fixture.svh').read_text().replace('m20v21_cpu_core dut(.*);',"m20v3_cpu_core dut(.debug_input_selected(),.debug_input_bank(),.commit_ce(1'b1),.master_hold(1'b1),.slave_open(1'b0),.*);")
(d/'tb/m20v21_tb_fixture.svh').write_text(s)
PY
cd "$D/xsim"
"$V/xvlog" --sv -i "$D/tb" "$R/rtl/m20/m20_pkg.sv" "$R/rtl/m20/m20_alu.sv" "$R/rtl/m20/m20_decoder.sv" "$R/rtl/m20/m20_control.sv" "$R/rtl/m20/m20_pc.sv" "$R/rtl/m20/m20_ar.sv" "$R/rtl/m20/m20_cpu_core.sv" "$R/rtl/modules/m20/v3/swc_v3_mux157.sv" "$R/rtl/modules/m20/v3/generated/m20v3_cpu_core.sv" "$R/sim/m20/rom_model.sv" "$R/sim/m20/ram_model.sv" "$R/sim/m20_v21/tb_m20v21_cpu.sv" > compile.log 2>&1
"$V/xelab" tb_m20v21_cpu -s shuffled --timescale 1ns/1ps > elaborate.log 2>&1
"$V/xsim" shuffled --tclbatch "$R/sim/oled_keys/run.tcl" --testplusarg "CASE_DIR=$D" --log simulation.log > console.log 2>&1
grep 'M20V21_CPU_PASS' simulation.log
"$P" -B -m m20.v21_verify compare --output "$D"
echo "M20_V3_SNAKE_SHUFFLED_PASS $D"
