#!/usr/bin/env bash
# Runs full functional guards AND all six delay/dead-time/skew profiles/negatives.
# A fresh output directory is mandatory; does not alter historical test evidence.
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec "$R/sim/scripts/run_m20_v23.sh" "$@"
