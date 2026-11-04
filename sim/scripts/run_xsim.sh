#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python_bin="${SWCELL_PYTHON:-python3}"
if [[ -z "${SWCELL_PYTHON:-}" && -x "$repo_root/build/venvs/python312/bin/python" ]]; then
  python_bin="$repo_root/build/venvs/python312/bin/python"
fi
for tool in xvlog xelab xsim "$python_bin"; do
  command -v "$tool" >/dev/null || { echo "Missing tool: $tool; source Vivado 2022.1/settings64.sh" >&2; exit 127; }
done
run_dir="$repo_root/build/sim/m11/functional"
mkdir -p "$run_dir"
cd "$run_dir"
mapfile -t sources < <(find "$repo_root/rtl/common" "$repo_root/rtl/modules/m11" "$repo_root/fpga/projects/m11/functional/rtl" "$repo_root/fpga/projects/diagnostics" "$repo_root/sim/models" "$repo_root/sim/m11" -maxdepth 2 -name '*.sv' | sort)
xvlog --sv "${sources[@]}" >compile.log 2>&1 || { cat compile.log; exit 1; }
xelab tb_m11 --snapshot m11_regression --timescale 1ns/1ps >elaborate.log 2>&1 || { cat elaborate.log; exit 1; }
for fault in 0 1 2 3; do
  xsim m11_regression --tclbatch "$repo_root/sim/scripts/run_all.tcl" \
    --testplusarg "FAULT=$fault" --testplusarg "OUTPUT=$run_dir/fault_$fault.jsonl" \
    --log "fault_$fault.log" >"fault_$fault.console.log" 2>&1 || { cat "fault_$fault.console.log"; exit 1; }
  # XSIM can return 0 after an HDL $fatal; require the explicit success sentinel too.
  if ! grep -q "REGRESSION_PASS fault=$fault " "fault_$fault.log"; then
    cat "fault_$fault.log"; exit 1
  fi
  "$python_bin" "$repo_root/sim/scripts/check_uart.py" "$run_dir/fault_$fault.jsonl" --fault "$fault"
done
xelab tb_m11 --snapshot m11_slow --timescale 1ns/1ps \
  --generic_top "CLK_HZ=20000000" --generic_top "BAUD=2500000" \
  --generic_top "STEP_NS=700" --generic_top "SYNC_STAGES=3" >slow_elaborate.log 2>&1 || { cat slow_elaborate.log; exit 1; }
xsim m11_slow --tclbatch "$repo_root/sim/scripts/run_all.tcl" \
  --testplusarg "FAULT=0" --testplusarg "OUTPUT=$run_dir/slow.jsonl" \
  --log slow.log >slow.console.log 2>&1 || { cat slow.console.log; exit 1; }
grep -q 'REGRESSION_PASS fault=0 ' slow.log || { cat slow.log; exit 1; }
"$python_bin" "$repo_root/sim/scripts/check_uart.py" "$run_dir/slow.jsonl" --fault 0
xelab tb_m11 --snapshot m11_board50 --timescale 1ns/1ps \
  --generic_top "CLK_HZ=50000000" --generic_top "BAUD=6250000" >board50_elaborate.log 2>&1 || { cat board50_elaborate.log; exit 1; }
xsim m11_board50 --tclbatch "$repo_root/sim/scripts/run_all.tcl" \
  --testplusarg "FAULT=0" --testplusarg "OUTPUT=$run_dir/board50.jsonl" \
  --log board50.log >board50.console.log 2>&1 || { cat board50.console.log; exit 1; }
grep -q 'REGRESSION_PASS fault=0 ' board50.log || { cat board50.log; exit 1; }
"$python_bin" "$repo_root/sim/scripts/check_uart.py" "$run_dir/board50.jsonl" --fault 0
xelab tb_power_on_reset --snapshot power_on_reset_unit --timescale 1ns/1ps >por_elaborate.log 2>&1 || { cat por_elaborate.log; exit 1; }
xsim power_on_reset_unit --tclbatch "$repo_root/sim/scripts/run_all.tcl" \
  --log por_unit.log >por_unit.console.log 2>&1 || { cat por_unit.console.log; exit 1; }
grep -q 'POWER_ON_RESET_PASS' por_unit.log || { cat por_unit.log; exit 1; }
xelab tb_uart --snapshot uart_unit --timescale 1ns/1ps >uart_elaborate.log 2>&1 || { cat uart_elaborate.log; exit 1; }
xsim uart_unit --tclbatch "$repo_root/sim/scripts/run_all.tcl" \
  --log uart_unit.log >uart_unit.console.log 2>&1 || { cat uart_unit.console.log; exit 1; }
grep -q 'UART_UNIT_PASS' uart_unit.log || { cat uart_unit.log; exit 1; }
"$repo_root/sim/scripts/run_uart_pin_id.sh"
"$python_bin" -B "$repo_root/tools/test/run_python_tests.py"
printf 'XSIM_REGRESSION_PASS (4 M11 scenarios + alternate timing + board 50MHz + UART 115200 + POR + dual pin-ID)\n'
