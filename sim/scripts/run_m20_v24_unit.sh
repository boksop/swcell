#!/usr/bin/env bash
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
V="${M20_VIVADO_BIN:-$HOME/AMDDesignTools/2026.1.1/Vivado/bin}"
P="${SWCELL_PYTHON:-$R/build/venvs/python312/bin/python}"
D="${M20V24_UNIT_DIR:-$R/build/m20_300/v24/unit_$(date +%Y%m%d_%H%M%S)}"
[[ ! -e "$D" ]] || { echo 'refusing existing unit directory';exit 1; }
mkdir -p "$D"
PYTHONPATH="$R/host/python" "$P" -B -m m20.v24_audit --output "$D/resource_audit.json"
for profile in nominal fast slow bad_skew;do
 mkdir -p "$D/$profile";cd "$D/$profile";defs=()
 case "$profile" in fast)defs=(-d V24_FAST);;slow)defs=(-d V24_SLOW);;bad_skew)defs=(-d V24_BAD_SKEW);;esac
 "$V/xvlog" --sv "${defs[@]}" "$R/rtl/m20/v23/swc_ms_bit_v23.sv" "$R/rtl/m20/v24/generated/swc157_phasegen_v24.sv" "$R/sim/m20_v24/tb_v24_generator.sv" > compile.log 2>&1
 "$V/xelab" tb_v24_generator -s generator --debug all --timescale 1ns/1ps > elaborate.log 2>&1
 "$V/xsim" generator --tclbatch "$R/sim/m20_v23/run_all.tcl" --log run.log > console.log 2>&1 || true
 if [[ "$profile" == bad_skew ]];then grep -q 'Fatal: V23_PHASE_OVERLAP' run.log
 else grep -q 'V24_GENERATOR_PASS.*illegal_recovered=8' run.log || { tail -25 run.log;exit 1; };fi
 echo "V24_UNIT_PASS profile=$profile"
done
