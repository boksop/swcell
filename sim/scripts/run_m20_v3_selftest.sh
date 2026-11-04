#!/usr/bin/env bash
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
P="${SWCELL_PYTHON:-$R/build/venvs/python312/bin/python}"
V="${M20_VIVADO_BIN:-$HOME/AMDDesignTools/2026.1.1/Vivado/bin}"
D="${M20V3_SELFTEST_OUTPUT:-$R/build/sim/m20_v3/selftest_$(date +%Y%m%d_%H%M%S)}"
[[ ! -e "$D" ]] || exit 1
mkdir -p "$D";D="$(cd "$D" && pwd)"
"$P" "$R/tools/m20/v3_selftest_program.py" --output "$D/programs"
cd "$D"
"$V/xvlog" --sv "$R/rtl/modules/m20/v3/generated/m20_v3_game_pkg.sv" "$R/rtl/modules/m20/v3/swc_v3_mux157.sv" "$R/rtl/modules/m20/v3/generated/m20v3_cpu_core.sv" "$R/rtl/modules/m20/v3/swc_m20_v3_memory.sv" "$R/rtl/modules/m20/v3/swc_m20_v3_system.sv" "$R/sim/m20_v3/tb_m20_v3_selftest.sv" > compile.log 2>&1
for name in isa_selftest illegal;do
 trap=0;[[ "$name" != illegal ]] || trap=1
 mkdir "$name"
 "$V/xelab" tb_m20_v3_selftest -s "$name" --timescale 1ns/1ps \
  --generic_top "PONG_FILE=$D/programs/$name.memh" --generic_top "SNAKE_FILE=$R/rtl/modules/m20/v3/generated/snake.memh" --generic_top "EXPECT_TRAP=$trap" > "$name/elaborate.log" 2>&1
 "$V/xsim" "$name" --tclbatch "$R/sim/oled_keys/run.tcl" --testplusarg "OUT=$D/$name" --log "$name/simulation.log" > "$name/console.log" 2>&1
 grep 'M20_V3_DIAGNOSTIC_ROM_PASS' "$name/simulation.log"
done
"$P" - "$D" <<'PY'
from pathlib import Path
import json,sys
d=Path(sys.argv[1]);e=json.loads((d/'programs/expected.json').read_text());r=json.loads((d/'isa_selftest/final_state.json').read_text())
for k,v in e['registers'].items():assert r[k]==v,(k,r[k],v)
assert r['micro']==e['cycles']+1 and r['retired']==e['retired'] and r['writes']==e['ram_writes']
# writememh emits // address comments; parse by complete lines.
ram=[int(s,16) for line in (d/'isa_selftest/final_ram.memh').read_text().splitlines() if not line.startswith('//') for s in line.split()]
assert ram==e['ram']
t=json.loads((d/'illegal/final_state.json').read_text());assert t['ustate']==7 and t['writes']==0 and t['retired']==0 and t['micro']==3
print('M20_V3_SELFTEST_ORACLE_PASS vectors=71 instructions='+str(e['retired']))
PY
