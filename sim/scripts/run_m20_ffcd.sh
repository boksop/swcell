#!/usr/bin/env bash
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
V="${M20_VIVADO_BIN:-$HOME/AMDDesignTools/2026.1.1/Vivado/bin}"
P="${SWCELL_PYTHON:-$R/build/venvs/python312/bin/python}"
D="${M20_FFCD_OUTPUT_DIR:-$R/build/m20_300/v24_ffcd/run_$(date +%Y%m%d_%H%M%S)}"
STAGE="${M20_FFCD_STAGE:-full}"
export PYTHONPATH="$R/host/python${PYTHONPATH:+:$PYTHONPATH}" PYTHONDONTWRITEBYTECODE=1
"$P" -B -m m20.ffcd_verify prepare --output "$D"
D="$(cd "$D" && pwd)"
compile_profile(){
 local profile="$1";mkdir -p "$D/$profile/xsim";cd "$D/$profile/xsim"
 local defs=();case "$profile" in *_logic)defs+=(-d FFCD_LOGIC_ONLY);;A_timed)defs+=(-d V23_DELAYED);;esac
 case "$profile" in C*)defs+=(-d FFCD_MODE_C);;esac
 "$V/xvlog" --sv -i "$R/sim/m20_ffcd/generated" -i "$R/sim/m20_ffcd" -i "$R/sim/m20_v23" "${defs[@]}" \
 "$R/rtl/m20/m20_pkg.sv" "$R/rtl/m20/m20_alu.sv" "$R/rtl/m20/m20_ar.sv" "$R/rtl/m20/m20_pc.sv" "$R/rtl/m20/m20_control.sv" "$R/rtl/m20/m20_decoder.sv" "$R/rtl/m20/m20_cpu_core.sv" \
 "$R/rtl/m20/v21/swc_mux157.sv" "$R/rtl/m20/v21/generated/m20v21_cpu_core.sv" \
 "$R/rtl/m20/v23/swc_ms_bit_v23.sv" "$R/rtl/m20/v23/swc_fpga_memory_adapter.sv" "$R/rtl/m20/v23/swc_two_phase_scheduler.sv" "$R/rtl/m20/v23/generated/m20v23_cpu_core.sv" \
 "$R/rtl/m20/v24_ffcd/swc_ffcd_service.sv" "$R/rtl/m20/v24_ffcd/swc_ffcd_run_control.sv" \
 "$R/sim/m20_ff16/swc_ff16_timing.sv" "$R/sim/m20_ffcd/swc_ffcd_ms_bit.sv" "$R/rtl/m20/v24_ffcd/generated/m20ffcd_cpu_core.sv" \
 "$R/sim/m20_ffcd/m20_ffcd_memory.sv" "$R/sim/m20_v23/m20_v23_fpga_memory.sv" "$R/sim/m20_v23/m20_v23_io_model.sv" \
 "$R/sim/m20_ffcd/generated/tb_m20ffcd_cpu.sv" "$R/sim/m20_ffcd/generated/tb_m20ffcd_mode_a.sv" "$R/sim/m20_ffcd/generated/tb_m20ffcd_memory.sv" "$R/sim/m20_ffcd/generated/tb_m20ffcd_illegal.sv" "$R/sim/m20_ffcd/tb_m20ffcd_control.sv" \
 "$R/sim/m20_v23/tb_m20v23_memory.sv" "$R/sim/m20_ffcd/tb_ffcd_service_unit.sv" "$R/sim/m20_ffcd/tb_ffcd_bad_service.sv" > compile.log 2>&1
}
run_top(){
 local top="$1" name="$2" marker="$3";shift 3
 "$V/xelab" "$top" -s "$top" --debug all --timescale 1ns/1ps > "$top.elaborate.log" 2>&1
 local tcl="$R/sim/m20_v23/run_all.tcl"
 if [[ "$top" == tb_m20ffcd_memory ]];then tcl="$R/sim/m20_ffcd/run_memory_wave.tcl";fi
 "$V/xsim" "$top" --tclbatch "$tcl" --log "$name.log" "$@" > "$name.console.log" 2>&1
 grep -q "$marker" "$name.log" || { tail -35 "$name.log";exit 1; }
 if grep -q 'Fatal:' "$name.log";then tail -35 "$name.log";exit 1;fi
 grep "$marker" "$name.log"
}
# C gate and minimum CPU BEFORE the full87 suites.
for profile in B_timed C_timed;do
 compile_profile "$profile"
 if [[ "$profile" == B_timed ]];then run_top tb_ffcd_service_unit service FFCD_SERVICE_UNIT_PASS;fi
 run_top tb_m20ffcd_memory memory 'M20FFCD_MEMORY_PASS checks=7' --testplusarg "EVENT_LOG=$D/$profile/xsim/service_events.csv"
 run_top tb_m20ffcd_control control M20FFCD_CONTROL_PASS
 run_top tb_m20ffcd_cpu smoke 'M20FFCD_CPU_PASS cases=2' --testplusarg "CASE_DIR=$D/$profile/smoke"
 "$P" -B -m m20.ffcd_verify compare --output "$D/$profile/smoke"
done
echo 'FFCD_C_GATE_VERIFIED memory7 + control + minimumCPU in B/C'
if [[ "$STAGE" == dev ]];then echo "FFCD_DEV_PASS output=$D";exit 0;fi
# Service-delay negatives must fail for their intended window violation.
cd "$D/B_timed/xsim"
"$V/xelab" tb_ffcd_bad_service -s bad_ram --debug all --timescale 1ns/1ps > bad_ram.elaborate.log 2>&1
"$V/xsim" bad_ram --tclbatch "$R/sim/m20_v23/run_all.tcl" --log bad_ram.log > bad_ram.console.log 2>&1 || true
grep -q 'Fatal: V23_RAM_RESPONSE_SETUP' bad_ram.log
"$V/xvlog" --sv -d FFCD_BAD_ROM -i "$R/sim/m20_ffcd/generated" -i "$R/sim/m20_ffcd" "$R/sim/m20_ffcd/tb_ffcd_bad_service.sv" > bad_rom.compile.log 2>&1
"$V/xelab" tb_ffcd_bad_service -s bad_rom --debug all --timescale 1ns/1ps > bad_rom.elaborate.log 2>&1
"$V/xsim" bad_rom --tclbatch "$R/sim/m20_v23/run_all.tcl" --log bad_rom.log > bad_rom.console.log 2>&1 || true
grep -q 'Fatal: V23_ROM_CHANGED_MASTER_OPEN' bad_rom.log
echo 'FFCD_SERVICE_NEGATIVES_DETECTED'
for profile in A_logic A_timed B_logic B_timed C_logic C_timed;do
 compile_profile "$profile"
 if [[ "$profile" == A* ]];then
  run_top tb_m20v23_memory memory 'M20V23_MEMORY_PASS checks=7';top=tb_m20ffcd_mode_a;marker=M20V23_CPU_PASS
 else
  if [[ "$profile" != B_timed && "$profile" != C_timed ]];then run_top tb_m20ffcd_memory memory 'M20FFCD_MEMORY_PASS checks=7';fi
  top=tb_m20ffcd_cpu;marker=M20FFCD_CPU_PASS
 fi
 for suite in instructions games pressure smoke;do
  run_top "$top" "$suite" "$marker" --testplusarg "CASE_DIR=$D/$profile/$suite"
  "$P" -B -m m20.ffcd_verify compare --output "$D/$profile/$suite"
 done
 if [[ "$profile" == B_timed || "$profile" == C_timed ]];then
  run_top tb_m20ffcd_illegal illegal 'M20FFCD_ILLEGAL_PASS words=65536 legal=15015 illegal=50521 actual_trap=50521 recovered=50521'
 fi
done
"$P" -B -m m20.ffcd_verify summarize --output "$D"
echo "FFCD_FULL_DIGITAL_PASS output=$D"
