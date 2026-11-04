#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
mkdir -p "$root/build/sim/m11/controls"
cd "$root/build/sim/m11/controls"
xvlog --sv "$root/rtl/common/swc_prbs31.sv" "$root/rtl/common/swc_snapshot_bridge.sv" \
 "$root/rtl/common/xilinx/swc_hs_pattern_driver.sv" "$root/rtl/common/xilinx/swc_hs_clocks.sv" \
 "$root/sim/phase2/tb_hs_controls.sv" "$root/sim/phase2/tb_hs_clock_grid.sv" >compile.log 2>&1 || { cat compile.log;exit 1; }
vivado_root="$(cd "$(dirname "$(command -v xvlog)")/.." && pwd)"
xvlog "$vivado_root/data/verilog/src/glbl.v" >>compile.log 2>&1
xelab tb_hs_controls glbl -L unisims_ver --snapshot controls --timescale 1ns/1ps >controls.elab.log 2>&1
xsim controls --tclbatch "$root/sim/scripts/run_all.tcl" --log controls.log >controls.console.log 2>&1
grep '^HS_CONTROLS_SIM_PASS ' controls.log || { cat controls.log;exit 1; }
for hz in 1000000 5000000 10000000 25000000 50000000 75000000 100000000 125000000 150000000 200000000; do
  name="grid_$hz"
  xelab tb_hs_clock_grid glbl -L unisims_ver --snapshot "$name" --timescale 1ns/1ps --generic_top "HZ=$hz" >"$name.elab.log" 2>&1 || { cat "$name.elab.log";exit 1; }
  xsim "$name" --tclbatch "$root/sim/scripts/run_all.tcl" --log "$name.log" >"$name.console.log" 2>&1 || { cat "$name.log";exit 1; }
  grep '^HS_CLOCK_GRID_PASS ' "$name.log" || { cat "$name.log";exit 1; }
done
echo PHASE2_CONTROLS_XSIM_PASS
