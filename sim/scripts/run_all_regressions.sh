#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
"$root/sim/scripts/run_xsim.sh"
"$root/sim/scripts/run_phase2.sh"
"$root/sim/scripts/run_phase2_controls.sh"
"$root/sim/scripts/run_phase2b.sh"
echo SWCELL_ALL_REGRESSIONS_PASS
