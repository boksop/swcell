#!/usr/bin/env bash
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
P="${SWCELL_PYTHON:-$R/build/venvs/python312/bin/python}"
V="${M20_VIVADO_BIN:-$HOME/AMDDesignTools/2026.1.1/Vivado/bin}"
OUT="${M20V21_OUTPUT_DIR:-$R/build/m20_300/v21/regression_20261102}"
export PYTHONPATH="$R/host/python${PYTHONPATH:+:$PYTHONPATH}" PYTHONDONTWRITEBYTECODE=1
# Python rejects historic paths before mkdir/compile writes.
"$P" -B -m m20.v21_verify prepare --output "$OUT"
OUT="$(cd "$OUT" && pwd)"
mkdir -p "$OUT/xsim"
cd "$OUT/xsim"
"$V/xvlog" --sv -i "$R/sim/m20_v21" \
 "$R/rtl/m20/m20_pkg.sv" "$R/rtl/m20/m20_alu.sv" "$R/rtl/m20/m20_decoder.sv" \
 "$R/rtl/m20/m20_control.sv" "$R/rtl/m20/m20_pc.sv" "$R/rtl/m20/m20_ar.sv" "$R/rtl/m20/m20_cpu_core.sv" \
 "$R/rtl/m20/v21/swc_mux157.sv" "$R/rtl/m20/v21/generated/m20v21_cpu_core.sv" \
 "$R/sim/m20/rom_model.sv" "$R/sim/m20/ram_model.sv" "$R/sim/m20/tb_m20_isa.sv" \
 "$R/sim/m20_v21/tb_m20v21_illegal.sv" "$R/sim/m20_v21/tb_m20v21_datapath.sv" \
 "$R/sim/m20_v21/tb_m20v21_memory.sv" "$R/sim/m20_v21/tb_m20v21_cpu.sv" > compile.log 2>&1
for top in tb_m20_isa tb_m20v21_illegal tb_m20v21_datapath tb_m20v21_memory tb_m20v21_cpu; do
 "$V/xelab" "$top" --snapshot "${top}_v21" --debug all --timescale 1ns/1ps > "$top.elaborate.log" 2>&1
done
run_test() {
 local top="$1" name="$2" marker="$3";shift 3
 "$V/xsim" "${top}_v21" --tclbatch "$R/sim/m20_v21/run_all.tcl" --log "$name.log" "$@" > "$name.console.log" 2>&1
 grep -q "$marker" "$name.log" || { tail -n 30 "$name.log";exit 1; }
}
run_test tb_m20_isa isa_v1 M20_ISA_PASS
run_test tb_m20v21_datapath datapath M20V21_DATAPATH_PASS
run_test tb_m20v21_illegal illegal M20V21_ILLEGAL_PASS
run_test tb_m20v21_memory memory M20V21_MEMORY_PASS
for suite in instructions games; do
 run_test tb_m20v21_cpu "$suite" M20V21_CPU_PASS --testplusarg "CASE_DIR=$OUT/$suite"
 "$P" -B -m m20.v21_verify compare --output "$OUT/$suite" > "$suite.compare.log" 2>&1
 cat "$suite.compare.log"
done
"$P" -B -m m20.v21_verify summarize --output "$OUT"
echo "M20_V21_REGRESSION_PASS output=$OUT"
