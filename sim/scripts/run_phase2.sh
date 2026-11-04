#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python_bin="${SWCELL_PYTHON:-python3}"
export PYTHONPATH="$root/host/python${PYTHONPATH:+:$PYTHONPATH}" PYTHONDONTWRITEBYTECODE=1
mkdir -p "$root/build/sim/m11/performance"
cd "$root/build/sim/m11/performance"
mapfile -t sources < <(find "$root/rtl/common" "$root/rtl/modules/m11/phase2" "$root/fpga/projects/m11/performance/rtl" "$root/sim/phase2" -name '*.sv' | sort)
xvlog --sv "${sources[@]}" >compile.log 2>&1 || { cat compile.log;exit 1; }
vivado_root="$(cd "$(dirname "$(command -v xvlog)")/.." && pwd)"
xvlog "$vivado_root/data/verilog/src/glbl.v" >>compile.log 2>&1
run_case() {
  local name="$1";shift
  xelab tb_m11_hs glbl -L unisims_ver --snapshot "$name" --timescale 1ns/1ps "$@" >"$name.elab.log" 2>&1 || { cat "$name.elab.log";exit 1; }
  xsim "$name" --tclbatch "$root/sim/scripts/run_all.tcl" --testplusarg "OUTPUT=$name.jsonl" --log "$name.log" >"$name.console.log" 2>&1 || { cat "$name.console.log";exit 1; }
  grep '^HS_SIM_PASS ' "$name.log" || { cat "$name.log";exit 1; }
  "$python_bin" - "$name.jsonl" <<'PY'
import json,sys
from pathlib import Path
# PYTHONPATH is resolved from the repository, independently of the output depth.
from swcell_capture import parse_record
records=[parse_record(x) for x in open(sys.argv[1])]
if records[0]['type']!='SWEEP_START' or records[-1]['type']!='SWEEP_COMPLETE':raise SystemExit('Missing UART envelope')
if len([x for x in records if x['type'] in ('PHASE_RESULT','FREQ_RESULT')])!=1:raise SystemExit('Wrong result count')
print('HS_UART_PARSE_PASS',sys.argv[1])
PY
}
run_case normal
run_case early_q --generic_top Q_PHASE=1
run_case early_qm --generic_top QM_PHASE=8
run_case fault_q --generic_top FAULT=1
run_case fault_qm --generic_top FAULT=2
run_case fault_both --generic_top FAULT=3
run_case zero --generic_top PATTERN=0
run_case one --generic_top PATTERN=1
run_case alternate --generic_top PATTERN=2
run_case pairs --generic_top PATTERN=3
run_case low_1mhz --generic_top FREQUENCY_HZ=1000000
run_case low_5mhz --generic_top FREQUENCY_HZ=5000000
run_case late_5mhz --generic_top FREQUENCY_HZ=5000000 --generic_top Q_PHASE=15 --generic_top QM_PHASE=15 --generic_top REQUIRE_ZERO=1
run_case late_10mhz --generic_top FREQUENCY_HZ=10000000 --generic_top Q_PHASE=15 --generic_top QM_PHASE=15 --generic_top REQUIRE_ZERO=1
run_case zero_phase --generic_top Q_PHASE=0 --generic_top QM_PHASE=0
run_case clock_loss --generic_top FAULT=4
run_case restart --generic_top FAULT=5
for hz in 10000000 50000000 75000000 100000000 125000000 150000000 200000000; do
  run_case "clock_$hz" --generic_top "FREQUENCY_HZ=$hz" --generic_top MASTER_NS=0.1 --generic_top SLAVE_NS=0.2
done
run_case million --generic_top TEST_BITS=1000000
xelab tb_capture_lane --snapshot capture64 --timescale 1ns/1ps >capture64.elab.log 2>&1
xsim capture64 --tclbatch "$root/sim/scripts/run_all.tcl" --log capture64.log >capture64.console.log 2>&1
grep '^CAPTURE64_SIM_PASS ' capture64.log || { cat capture64.log;exit 1; }
echo PHASE2_XSIM_PASS
