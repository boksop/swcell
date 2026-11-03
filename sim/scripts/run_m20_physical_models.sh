#!/usr/bin/env bash
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
V="${M20_VIVADO_BIN:-$HOME/AMDDesignTools/2026.1.1/Vivado/bin}"
OUT="${M20_PHYSICAL_MODEL_OUTPUT:-$R/build/m20_300/v21/physical_models}"
mkdir -p "$OUT";cd "$OUT"
"$V/xvlog" -sv "$R/rtl/m20/v21/swc_mux157.sv" "$R/rtl/m20/v21/generated/m20v21_cpu_core.sv" \
 "$R/rtl/m20/interface/m20_fpga_memory_adapter.sv" "$R/sim/m20_physical/swc_mux157_timed.sv" \
 "$R/sim/m20_physical/tb_m20_dff_timing.sv" "$R/sim/m20_physical/tb_m20_fpga_adapter.sv" > compile.log 2>&1
for top in tb_m20_dff_timing tb_m20_fpga_adapter; do
 "$V/xelab" "$top" -s "$top" --debug all > "$top.elaborate.log" 2>&1
 "$V/xsim" "$top" -runall > "$top.log" 2>&1
done
grep -q NONOVERLAP_MODEL_PASS tb_m20_dff_timing.log
grep -q EXPECTED_RACE_OBSERVED tb_m20_dff_timing.log
grep -q M20_DFF_TIMING_MODEL_PASS tb_m20_dff_timing.log
grep -q M20_FPGA_ADAPTER_PASS tb_m20_fpga_adapter.log
echo M20_PHYSICAL_MODELS_PASS_ILLUSTRATIVE_ONLY
