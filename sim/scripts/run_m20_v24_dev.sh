#!/usr/bin/env bash
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)";V="${M20_VIVADO_BIN:-$HOME/AMDDesignTools/2026.1.1/Vivado/bin}"
P="$R/build/venvs/python312/bin/python";D="${M20V24_DEV_DIR:?new output required}"
[[ ! -e "$D" ]] || exit 1
PYTHONPATH="$R/host/python" "$P" -B -m m20.rtl_regression prepare --output "$D"
mkdir -p "$D/xsim";cd "$D/xsim"
"$V/xvlog" --sv -i "$R/sim/m20_v24" -d V24_TIMED \
 "$R/rtl/m20/m20_pkg.sv" "$R/rtl/m20/m20_alu.sv" "$R/rtl/m20/m20_ar.sv" "$R/rtl/m20/m20_pc.sv" "$R/rtl/m20/m20_control.sv" "$R/rtl/m20/m20_decoder.sv" "$R/rtl/m20/m20_cpu_core.sv" \
 "$R/rtl/m20/v21/swc_mux157.sv" "$R/rtl/m20/v21/generated/m20v21_cpu_core.sv" "$R/rtl/m20/v23/swc_ms_bit_v23.sv" "$R/rtl/m20/v23/swc_two_phase_scheduler.sv" "$R/rtl/m20/v23/generated/m20v23_cpu_core.sv" \
 "$R/rtl/m20/v24/generated/swc157_phasegen_v24.sv" "$R/rtl/m20/v24/swc_v24_memory_service.sv" "$R/sim/m20_v24/m20_v24_fpga_memory.sv" "$R/sim/m20_v23/m20_v23_io_model.sv" \
 "$R/sim/m20_v24/tb_m20v24_cpu.sv" "$R/sim/m20_v24/tb_m20v24_memory.sv" "$R/sim/m20_v24/tb_m20v24_illegal.sv" > compile.log 2>&1
for top in memory cpu;do
 "$V/xelab" "tb_m20v24_$top" -s "$top" --debug all --timescale 1ns/1ps > "$top.elaborate.log" 2>&1
 args=();if [[ "$top" == cpu ]];then args=(--testplusarg "CASE_DIR=$D/instructions");fi
 "$V/xsim" "$top" --tclbatch "$R/sim/m20_v23/run_all.tcl" --log "$top.log" "${args[@]}" > "$top.console.log" 2>&1
 grep -q "M20V24_${top^^}_PASS" "$top.log" || { tail -30 "$top.log";exit 1; }
done
