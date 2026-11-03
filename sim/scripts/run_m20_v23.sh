#!/usr/bin/env bash
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
P="${SWCELL_PYTHON:-$R/build/venvs/python312/bin/python}"
V="${M20_VIVADO_BIN:-$HOME/AMDDesignTools/2026.1.1/Vivado/bin}"
OUT="${M20V23_OUTPUT_DIR:-$R/build/m20_300/v23/run_$(date +%Y%m%d_%H%M%S)}"
export PYTHONPATH="$R/host/python${PYTHONPATH:+:$PYTHONPATH}" PYTHONDONTWRITEBYTECODE=1
"$P" -B -m m20.v23_verify prepare --output "$OUT"
OUT="$(cd "$OUT" && pwd)"
for profile in zero delayed reduced max_delay master_late slave_early; do
 D="$OUT/$profile/xsim";mkdir -p "$D";cd "$D"
 defines=();if [[ "$profile" != zero ]];then defines+=(-d V23_DELAYED);fi
 if [[ "$profile" == reduced ]];then defines+=(-d V23_REDUCED_DEAD);fi
 if [[ "$profile" == max_delay ]];then defines+=(-d V23_MAX_DELAY);fi
 if [[ "$profile" == master_late ]];then defines+=(-d V23_MASTER_LATE);fi
 if [[ "$profile" == slave_early ]];then defines+=(-d V23_SLAVE_EARLY);fi
 "$V/xvlog" --sv -i "$R/sim/m20_v23" "${defines[@]}" \
 "$R/rtl/m20/m20_pkg.sv" "$R/rtl/m20/m20_alu.sv" "$R/rtl/m20/m20_ar.sv" "$R/rtl/m20/m20_pc.sv" "$R/rtl/m20/m20_control.sv" "$R/rtl/m20/m20_decoder.sv" "$R/rtl/m20/m20_cpu_core.sv" \
 "$R/rtl/m20/v21/swc_mux157.sv" "$R/rtl/m20/v21/generated/m20v21_cpu_core.sv" \
 "$R/rtl/m20/v23/swc_fpga_memory_adapter.sv" "$R/rtl/m20/v23/swc_ms_bit_v23.sv" "$R/rtl/m20/v23/swc_two_phase_scheduler.sv" "$R/rtl/m20/v23/generated/m20v23_cpu_core.sv" \
 "$R/sim/m20_v23/m20_v23_fpga_memory.sv" "$R/sim/m20_v23/m20_v23_io_model.sv" \
 "$R/sim/m20_v23/tb_m20v23_cpu.sv" "$R/sim/m20_v23/tb_m20v23_memory.sv" "$R/sim/m20_v23/tb_m20v23_illegal.sv" \
 "$R/sim/m20_v23/tb_m20v23_bad_window.sv" "$R/sim/m20_v23/tb_m20v23_step.sv" "$R/sim/m20_v23/tb_m20v23_scheduler.sv" "$R/sim/m20_v23/tb_m20v23_penetration.sv" > compile.log 2>&1
 run_top() {
  local top="$1" name="$2" marker="$3";shift 3
  "$V/xelab" "$top" -s "$top" --debug all --timescale 1ns/1ps > "$top.elaborate.log" 2>&1
  local tcl="$R/sim/m20_v23/run_all.tcl"
  if [[ "$top" == tb_m20v23_penetration ]];then tcl="$R/sim/m20_v23/run_penetration_wave.tcl";fi
  "$V/xsim" "$top" --tclbatch "$tcl" --log "$name.log" "$@" > "$name.console.log" 2>&1
  grep -q "$marker" "$name.log" || { tail -n 35 "$name.log";exit 1; }
  grep "$marker" "$name.log"
 }
 if [[ "$profile" == zero ]];then
  run_top tb_m20v23_scheduler scheduler M20V23_SCHEDULER_PASS
  run_top tb_m20v23_step step M20V23_STEP_PASS
  run_top tb_m20v23_penetration penetration M20V23_PENETRATION_PASS
  run_top tb_m20v23_memory memory M20V23_MEMORY_PASS
  "$V/xelab" tb_m20v23_bad_window -s bad_ram --debug all --timescale 1ns/1ps > bad_ram.elaborate.log 2>&1
  "$V/xsim" bad_ram --tclbatch "$R/sim/m20_v23/run_all.tcl" --log bad_ram.log > bad_ram.console.log 2>&1 || true
  grep -q 'Fatal: V23_RAM_RESPONSE_SETUP' bad_ram.log
  "$V/xvlog" --sv -d V23_BAD_ROM -i "$R/sim/m20_v23" "$R/sim/m20_v23/tb_m20v23_bad_window.sv" > bad_rom.compile.log 2>&1
  "$V/xelab" tb_m20v23_bad_window -s bad_rom --debug all --timescale 1ns/1ps > bad_rom.elaborate.log 2>&1
  "$V/xsim" bad_rom --tclbatch "$R/sim/m20_v23/run_all.tcl" --log bad_rom.log > bad_rom.console.log 2>&1 || true
  grep -q 'Fatal: V23_ROM_CHANGED_MASTER_OPEN' bad_rom.log
  run_top tb_m20v23_illegal illegal M20V23_ILLEGAL_PASS
  suites=(instructions games pressure)
 elif [[ "$profile" == delayed ]];then
  run_top tb_m20v23_memory memory M20V23_MEMORY_PASS
  suites=(instructions games pressure)
 else suites=(pressure);fi
 for suite in "${suites[@]}";do
  run_top tb_m20v23_cpu "$suite" M20V23_CPU_PASS --testplusarg "CASE_DIR=$OUT/$profile/$suite"
  "$P" -B -m m20.v23_verify compare --output "$OUT/$profile/$suite"
 done
done
# Assert-enabled negative must be detected, irrespective of XSIM's process exit code.
D="$OUT/negative/xsim";mkdir -p "$D";cd "$D"
"$V/xvlog" --sv -d V23_EXPECT_FATAL "$R/rtl/m20/v23/swc_ms_bit_v23.sv" "$R/sim/m20_v23/tb_m20v23_penetration.sv" > compile.log 2>&1
"$V/xelab" tb_m20v23_penetration -s overlap --debug all --timescale 1ns/1ps > elaborate.log 2>&1
"$V/xsim" overlap --tclbatch "$R/sim/m20_v23/run_all.tcl" --log overlap.log > console.log 2>&1 || true
grep -q 'Fatal: V23_PHASE_OVERLAP' overlap.log
if grep -q M20V23_PENETRATION_PASS overlap.log;then exit 1;fi
"$P" -B -m m20.v23_verify summarize --output "$OUT"
"$P" -B "$R/tools/m20/v23_evidence.py" --run "$OUT" --output "$OUT/readable_evidence"
echo "M20_V23_REGRESSION_PASS output=$OUT"
