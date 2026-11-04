#!/usr/bin/env bash
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
V="${M20_VIVADO_BIN:-$HOME/AMDDesignTools/2026.1.1/Vivado/bin}"
P="${SWCELL_PYTHON:-$R/build/venvs/python312/bin/python}"
D="${M20V24_OUTPUT_DIR:-$R/build/m20_300/v24/run_$(date +%Y%m%d_%H%M%S)}"
export PYTHONPATH="$R/host/python${PYTHONPATH:+:$PYTHONPATH}" PYTHONDONTWRITEBYTECODE=1
"$P" -B -m m20.v24_verify prepare --output "$D"
D="$(cd "$D" && pwd)"
# Unit/negative gate first; no CPU long regression if interlock tests fail.
M20V24_UNIT_DIR="$D/unit" "$R/sim/scripts/run_m20_v24_unit.sh"
for profile in A_zero B_zero C_zero A_timed B_timed C_timed B_slow;do
 mkdir -p "$D/$profile/xsim";cd "$D/$profile/xsim"
 defs=();case "$profile" in A*)defs+=(-d V24_MODE_A);;C*)defs+=(-d V24_MODE_C);;esac
 case "$profile" in *_timed)defs+=(-d V24_TIMED);;*_slow)defs+=(-d V24_SLOW_CPU);;esac
 "$V/xvlog" --sv -i "$R/sim/m20_v24" "${defs[@]}" \
 "$R/rtl/m20/m20_pkg.sv" "$R/rtl/m20/m20_alu.sv" "$R/rtl/m20/m20_ar.sv" "$R/rtl/m20/m20_pc.sv" "$R/rtl/m20/m20_control.sv" "$R/rtl/m20/m20_decoder.sv" "$R/rtl/m20/m20_cpu_core.sv" \
 "$R/rtl/m20/v21/swc_mux157.sv" "$R/rtl/m20/v21/generated/m20v21_cpu_core.sv" "$R/rtl/m20/v23/swc_ms_bit_v23.sv" "$R/rtl/m20/v23/swc_two_phase_scheduler.sv" "$R/rtl/m20/v23/generated/m20v23_cpu_core.sv" \
 "$R/rtl/m20/v24/generated/swc157_phasegen_v24.sv" "$R/rtl/m20/v24/swc_v24_memory_service.sv" "$R/sim/m20_v24/m20_v24_fpga_memory.sv" "$R/sim/m20_v23/m20_v23_io_model.sv" \
 "$R/sim/m20_v24/tb_m20v24_cpu.sv" "$R/sim/m20_v24/tb_m20v24_memory.sv" "$R/sim/m20_v24/tb_m20v24_illegal.sv" > compile.log 2>&1
 run_top(){
  local top="$1" name="$2" marker="$3";shift 3
  "$V/xelab" "$top" -s "$top" --debug all --timescale 1ns/1ps > "$top.elaborate.log" 2>&1
  "$V/xsim" "$top" --tclbatch "$R/sim/m20_v23/run_all.tcl" --log "$name.log" "$@" > "$name.console.log" 2>&1
  grep -q "$marker" "$name.log" || { tail -30 "$name.log";exit 1; }
  grep "$marker" "$name.log"
 }
 if [[ "$profile" != B_slow ]];then run_top tb_m20v24_memory memory M20V24_MEMORY_PASS;fi
 if [[ "$profile" == B_timed ]];then run_top tb_m20v24_illegal illegal M20V24_ILLEGAL_PASS;fi
 if [[ "$profile" == B_slow ]];then suites=(pressure);else suites=(instructions games pressure);fi
 for suite in "${suites[@]}";do
  run_top tb_m20v24_cpu "$suite" M20V24_CPU_PASS --testplusarg "CASE_DIR=$D/$profile/$suite"
  "$P" -B -m m20.v24_verify compare --output "$D/$profile/$suite"
 done
done
"$P" -B -m m20.v24_verify summarize --output "$D"
echo "M20_V24_REGRESSION_PASS output=$D"
