#!/usr/bin/env bash
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
P="${SWCELL_PYTHON:-$R/build/venvs/python312/bin/python}"
V="${M20_VIVADO_BIN:-$HOME/AMDDesignTools/2026.1.1/Vivado/bin}"
D="${M20V31_UNITS_OUTPUT:-$R/build/sim/m20_v31/units_$(date +%Y%m%d_%H%M%S)}"
[[ ! -e "$D" ]] || exit 1
mkdir -p "$D";D="$(cd "$D" && pwd)";export PYTHONPATH="$R/host/python"
"$P" -B - "$D" <<'PY'
from m20 import assemble
from pathlib import Path
import sys
Path(sys.argv[1],'probe.memh').write_text(assemble('LDI 9\nST 42\nHALT').memh)
PY
cd "$D"
"$V/xvlog" --sv "$R/rtl/common/swc_input_sync.sv" "$R/rtl/modules/m20/v3/swc_v3_mux157.sv" \
 "$R/rtl/modules/m20/v3/generated/m20v3_cpu_core.sv" \
 "$R/rtl/modules/m20/v31/swc_m20_v31_gpio.sv" "$R/rtl/modules/m20/v31/swc_m20_v31_memory.sv" \
 "$R/rtl/modules/m20/v31/swc_m20_v31_service.sv" "$R/sim/m20_v31/tb_m20_v31_units.sv" > compile.log 2>&1
for name in gpio memory control;do
 args=();[[ "$name" == gpio ]] || args+=(--generic_top "ROM_FILE=$D/probe.memh")
 "$V/xelab" "tb_m20_v31_$name" -s "$name" --timescale 1ns/1ps "${args[@]}" > "$name.elaborate.log" 2>&1
 "$V/xsim" "$name" --tclbatch "$R/sim/oled_keys/run.tcl" --log "$name.log" > "$name.console.log" 2>&1
 grep "M20_V31_.*_PASS" "$name.log"
 ! grep -q 'Fatal:' "$name.log"
done
