#!/usr/bin/env bash
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
V="${M20_VIVADO_BIN:-$HOME/AMDDesignTools/2026.1.1/Vivado/bin}"
P="${SWCELL_PYTHON:-$R/build/venvs/python312/bin/python}"
D="${M20_FF16_OUTPUT_DIR:-$R/build/m20_300/v24_ff16/small_$(date +%Y%m%d_%H%M%S)}"
export PYTHONPATH="$R/host/python${PYTHONPATH:+:$PYTHONPATH}" PYTHONDONTWRITEBYTECODE=1
"$P" -B -m m20.ff16_timing prepare --output "$D"
D="$(cd "$D" && pwd)"
"$P" -B -m m20.ff16_structure --output "$D/structure"
mkdir -p "$D/xsim";cd "$D/xsim"
"$V/xvlog" --sv "$R/rtl/m20/v24_ff16/swc_ff16_mux157.sv" "$R/rtl/m20/v24_ff16/swc_ff16_phasegen.sv" "$R/sim/m20_ff16_static/tb_ff16_structure.sv" "$R/sim/m20_ff16/swc_ff16_timing.sv" "$R/sim/m20_ff16/tb_ff16_model.sv" "$R/sim/m20_ff16/tb_ff16.sv" > compile.log 2>&1
"$V/xelab" tb_ff16_structure -s structure --debug all --timescale 1ns/1ps > structure.elaborate.log 2>&1
"$V/xsim" structure --tclbatch "$R/sim/m20_v23/run_all.tcl" --log structure.log > structure.console.log 2>&1
grep -q 'FF16_STATIC_LOGIC_VERIFIED vectors=24' structure.log || { tail -30 structure.log;exit 1; }
"$V/xelab" tb_ff16_model -s pin_model --debug all --timescale 1ns/1ps > model.elaborate.log 2>&1
"$V/xsim" pin_model --tclbatch "$R/sim/m20_v23/run_all.tcl" --log pin_model.log > model.console.log 2>&1
grep -q FF16_PIN_MODEL_VERIFIED pin_model.log || { tail -30 pin_model.log;exit 1; }
for tap in 4 8 12 16;do
 "$V/xelab" "tb_ff16_tap$tap" -s "tap$tap" --debug all --timescale 1ns/1ps > "tap$tap.elaborate.log" 2>&1
 "$V/xsim" "tap$tap" --tclbatch "$R/sim/m20_ff16/run_timing.tcl" --testplusarg "CASES=$D/tap$tap" --log "tap$tap.log" > "tap$tap.console.log" 2>&1
 grep -q "FF16_SMALL_COMPLETE tap=$tap cases=14" "tap$tap.log" || { tail -35 "tap$tap.log";exit 1; }
 mv timing.vcd "$D/tap$tap/timing.vcd"
 grep FF16_CASE "tap$tap.log"
done
"$P" -B -m m20.ff16_timing summarize --output "$D"
echo "FF16_A_B_COMPLETE output=$D"
echo 'CPU C/D are intentionally NOT launched by this entry; inspect project_gate first.'
