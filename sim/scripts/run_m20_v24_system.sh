#!/usr/bin/env bash
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
P="${SWCELL_PYTHON:-$R/build/venvs/python312/bin/python}"
D="${M20_FFCD_OUTPUT_DIR:-$R/build/m20_300/v24_ffcd/system_$(date +%Y%m%d_%H%M%S)}"
export PYTHONPATH="$R/host/python${PYTHONPATH:+:$PYTHONPATH}" PYTHONDONTWRITEBYTECODE=1
BLINE="${M20_FFCD_BASELINE:-$D.baseline.json}"
if [[ "${M20_FFCD_RESUME_FINISH:-0}" == 1 ]];then
 [[ -f "$D/verification.json" ]] || { echo 'No completed C/D evidence to finish';exit 1; }
 if [[ ! -f "$BLINE" ]];then BLINE="$R/build/m20_300/v24_ffcd/baseline_20261104.json";fi
else
 "$P" -B "$R/tools/m20/ffcd_checkpoint.py" --output "$BLINE"
 M20_FFCD_OUTPUT_DIR="$D" M20_FFCD_STAGE=full bash "$R/sim/scripts/run_m20_ffcd.sh"
fi
D="$(cd "$D" && pwd)"
name="$(basename "$D")"
N="${M20_FFCD_NEG_SMALL:-$R/build/m20_300/v24_ff16/${name}_ffcd_negative_small}"
Q="${M20_FFCD_NEG_CONES:-$R/build/m20_300/v24_ff16/${name}_ffcd_negative_cones}"
M20_FF16_OUTPUT_DIR="$N" bash "$R/sim/scripts/run_m20_ff16_small.sh" > "$D/negative_small.console.log" 2>&1
M20_FF16_REVIEW_OUTPUT_DIR="$Q" bash "$R/sim/scripts/run_m20_ff16_cones_replay.sh" > "$D/negative_cones.console.log" 2>&1
"$P" -B "$R/tools/test/run_python_tests.py" > "$D/python_tests.log" 2>&1
"$P" -B "$R/tools/m20/ffcd_evidence.py" --run "$D" --output "$D/readable_evidence" --negative-small "$N" --negative-cones "$Q" --baseline "$BLINE"
echo "M20_V24_DIGITAL_SYSTEM_COMPLETE evidence=$D/readable_evidence ; physical_timing=NOT_VERIFIED ; no_commit_tag_remote"
