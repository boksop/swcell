#!/usr/bin/env bash
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
P="${SWCELL_PYTHON:-$R/build/venvs/python312/bin/python}"
V="${M20_VIVADO_BIN:-$HOME/AMDDesignTools/2026.1.1/Vivado/bin}"
OUT="${M20V3_CORE_OUTPUT:-$R/build/sim/m20_v3/core_$(date +%Y%m%d_%H%M%S)}"
MODE="${M20V3_STORAGE_MODE:-FUNCTIONAL_STORAGE}"
[[ "$MODE" == FUNCTIONAL_STORAGE || "$MODE" == STRICT_MUX ]] || exit 1
[[ ! -e "$OUT" ]] || { echo 'Use fresh V3 output';exit 1; }
export PYTHONPATH="$R/host/python" PYTHONDONTWRITEBYTECODE=1
"$P" -B -m m20.v21_verify prepare --output "$OUT"
OUT="$(cd "$OUT" && pwd)";mkdir -p "$OUT/tb" "$OUT/generated" "$OUT/xsim"
"$P" "$R/tools/m20/v3_generate.py" --output "$OUT/generated"
"$P" - "$R" "$OUT" "$MODE" <<'PY'
from pathlib import Path
import re,sys
r,o=map(Path,sys.argv[1:3]);mode=sys.argv[3]
for p in (r/'sim/m20_v21').iterdir():
 if p.suffix in ('.sv','.svh'):
  original=p.read_text()
  binding='m20v3_cpu_core dut(.debug_input_selected(),.debug_input_bank(),.commit_ce(1\'b1),.master_hold(1\'b1),.slave_open(1\'b0),.*);'
  if mode=='STRICT_MUX':
   binding='''reg v3_h=0,v3_s=0;
always @(posedge clk) begin v3_h=1;#0.01;v3_s=1;end
always @(negedge clk) begin v3_s=0;#0.01;v3_h=0;end
m20v3_cpu_core #(.STORAGE_MODE("STRICT_MUX")) dut(.debug_input_selected(),.debug_input_bank(),.commit_ce(1'b1),.master_hold(v3_h),.slave_open(v3_s),.*);'''
   # Test-only initialization of latch outputs uses force/release rather than a
   # procedural assignment to a net. No CPU logic or expected values change.
   original=re.sub(r'(?<![\w])dut\.(pc_reg|ar_reg|a_reg|z_reg|c_reg|gpo_reg|state_reg)=([^;]+);',
       r'force dut.\1=\2; #100ps; release dut.\1;',original)
   original=original.replace('#1ps','#100ps')
  s=original.replace('m20v21_cpu_core dut(.*);',binding)
  (o/'tb'/p.name).write_text(s)
PY
cd "$OUT/xsim"
"$V/xvlog" --sv -i "$OUT/tb" \
 "$R/rtl/m20/m20_pkg.sv" "$R/rtl/m20/m20_alu.sv" "$R/rtl/m20/m20_decoder.sv" \
 "$R/rtl/m20/m20_control.sv" "$R/rtl/m20/m20_pc.sv" "$R/rtl/m20/m20_ar.sv" "$R/rtl/m20/m20_cpu_core.sv" \
 "$R/rtl/modules/m20/v3/swc_v3_mux157.sv" "$OUT/generated/m20v3_cpu_core.sv" \
 "$R/sim/m20/rom_model.sv" "$R/sim/m20/ram_model.sv" "$R/sim/m20/tb_m20_isa.sv" \
 "$OUT/tb/tb_m20v21_illegal.sv" "$OUT/tb/tb_m20v21_datapath.sv" "$OUT/tb/tb_m20v21_memory.sv" "$OUT/tb/tb_m20v21_cpu.sv" > compile.log 2>&1
run_test() {
 local top="$1" name="$2" marker="$3";shift 3
 "$V/xelab" "$top" --snapshot "$name" --debug all --timescale 1ns/1ps > "$name.elaborate.log" 2>&1
 "$V/xsim" "$name" --tclbatch "$R/sim/m20_v21/run_all.tcl" --log "$name.log" "$@" > "$name.console.log" 2>&1
 grep -q "$marker" "$name.log"
 ! grep -q 'Fatal:' "$name.log"
}
run_test tb_m20_isa isa M20_ISA_PASS
run_test tb_m20v21_datapath datapath M20V21_DATAPATH_PASS
run_test tb_m20v21_illegal illegal M20V21_ILLEGAL_PASS
run_test tb_m20v21_memory memory M20V21_MEMORY_PASS
for suite in instructions games;do
 run_test tb_m20v21_cpu "$suite" M20V21_CPU_PASS --testplusarg "CASE_DIR=$OUT/$suite"
 "$P" -B -m m20.v21_verify compare --output "$OUT/$suite" > "$suite.compare.log" 2>&1
 cat "$suite.compare.log"
done
echo "M20_V3_CORE_REGRESSION_PASS mode=$MODE $OUT"
