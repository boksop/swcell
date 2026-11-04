#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
for tool in xvlog xelab xsim; do
  command -v "$tool" >/dev/null || { echo "Missing $tool; source Vivado 2022.1/settings64.sh" >&2; exit 127; }
done
mkdir -p "$repo_root/build/sim/diagnostics/uart_pin_id"
cd "$repo_root/build/sim/diagnostics/uart_pin_id"
xvlog --sv "$repo_root/rtl/common/swc_power_on_reset.sv" \
  "$repo_root/rtl/common/swc_uart_tx.sv" "$repo_root/rtl/common/swc_uart_text_beacon.sv" \
  "$repo_root/fpga/projects/diagnostics/uart_pin_id/rtl/swcell_uart_pin_id_top.sv" \
  "$repo_root/sim/m11/tb_uart_pin_id.sv" >compile.log 2>&1 || { cat compile.log; exit 1; }
xelab tb_uart_pin_id --snapshot uart_pin_id --timescale 1ns/1ps >elaborate.log 2>&1 || { cat elaborate.log; exit 1; }
xsim uart_pin_id --tclbatch "$repo_root/sim/scripts/run_all.tcl" --log simulation.log \
  >simulation.console.log 2>&1 || { cat simulation.console.log; exit 1; }
grep -q '^UART_PIN_ID_SIM_PASS ' simulation.log || { cat simulation.log; exit 1; }
echo 'UART_PIN_ID_REGRESSION_PASS'
