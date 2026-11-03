#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
mkdir -p "$root/build/xsim_phase2b"
cd "$root/build/xsim_phase2b"
mapfile -t sources < <(find "$root/rtl/common" "$root/rtl/modules/m11/phase2" -name '*.sv' | sort)
xvlog --sv "${sources[@]}" "$root/sim/phase2/tb_phase2b.sv" >compile.log 2>&1 || { cat compile.log;exit 1; }
vivado_root="$(cd "$(dirname "$(command -v xvlog)")/.." && pwd)"
xvlog "$vivado_root/data/verilog/src/glbl.v" >>compile.log 2>&1
for hz in 75000000 100000000 125000000; do
  name="phase2b_$hz"
  xelab tb_phase2b glbl -L unisims_ver --snapshot "$name" --timescale 1ns/1ps --generic_top "HZ=$hz" >"$name.elab.log" 2>&1 || { cat "$name.elab.log";exit 1; }
  xsim "$name" --tclbatch "$root/sim/scripts/run_all.tcl" --log "$name.log" >"$name.console.log" 2>&1 || { cat "$name.log";exit 1; }
  grep '^PHASE2B_XSIM_PASS ' "$name.log" || { cat "$name.log";exit 1; }
done
PYTHONDONTWRITEBYTECODE=1 "$root/.venv/bin/python" -m unittest discover -s "$root/host/python/tests" -p 'test_phase2b.py' -v
echo PHASE2B_REGRESSION_PASS
