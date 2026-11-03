#!/usr/bin/env bash
# M20-only non-project XSIM regression. Never invokes synthesis or board tools.
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"
python_bin="${SWCELL_PYTHON:-$repo_root/build/venvs/python312/bin/python}"
if [[ ! -x "$python_bin" ]]; then python_bin="${SWCELL_PYTHON:-python3}"; fi
if [[ -n "${M20_VIVADO_BIN:-}" ]]; then
  vivado_bin="$M20_VIVADO_BIN"
elif [[ -n "${XILINX_VIVADO:-}" && -x "$XILINX_VIVADO/bin/xvlog" ]]; then
  vivado_bin="$XILINX_VIVADO/bin"
elif command -v xvlog >/dev/null 2>&1; then
  vivado_bin="$(dirname "$(command -v xvlog)")"
else
  vivado_bin="$HOME/AMDDesignTools/2026.1.1/Vivado/bin"
fi
for tool in xvlog xelab xsim; do
  [[ -x "$vivado_bin/$tool" ]] || { echo "Missing $tool; set M20_VIVADO_BIN to Vivado 2026.1 bin" >&2; exit 127; }
done
output_root="${M20_OUTPUT_DIR:-$repo_root/build/m20_300/v1}"
mkdir -p "$output_root"
output_root="$(cd "$output_root" && pwd)"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$repo_root/host/python${PYTHONPATH:+:$PYTHONPATH}"
export MPLCONFIGDIR="$output_root/matplotlib"
"$vivado_bin/xvlog" --version > "$output_root/tool_version.log" 2>&1
if ! grep -q '2026\.1' "$output_root/tool_version.log"; then
  cat "$output_root/tool_version.log" >&2
  echo 'M20 V1 requires the requested XSIM 2026.1 family; select it explicitly.' >&2
  exit 2
fi
"$python_bin" -B -m unittest discover -s "$repo_root/host/python/tests" -v \
  > "$output_root/python_tests.log" 2>&1 || { tail -n 100 "$output_root/python_tests.log"; exit 1; }
"$python_bin" -B -m m20.rtl_regression prepare --output "$output_root" \
  > "$output_root/prepare.log" 2>&1 || { cat "$output_root/prepare.log"; exit 1; }
mkdir -p "$output_root/xsim"
cd "$output_root/xsim"
sources=(
  "$repo_root/rtl/m20/m20_pkg.sv"
  "$repo_root/rtl/m20/m20_alu.sv"
  "$repo_root/rtl/m20/m20_decoder.sv"
  "$repo_root/rtl/m20/m20_control.sv"
  "$repo_root/rtl/m20/m20_pc.sv"
  "$repo_root/rtl/m20/m20_ar.sv"
  "$repo_root/rtl/m20/m20_cpu_core.sv"
  "$repo_root/sim/m20/rom_model.sv"
  "$repo_root/sim/m20/ram_model.sv"
  "$repo_root/sim/m20/tb_m20_isa.sv"
  "$repo_root/sim/m20/tb_m20_memory.sv"
  "$repo_root/sim/m20/tb_m20_cpu.sv"
)
"$vivado_bin/xvlog" --sv -i "$repo_root/sim/m20" "${sources[@]}" > compile.log 2>&1 || { cat compile.log; exit 1; }
for top in tb_m20_isa tb_m20_memory tb_m20_cpu; do
  "$vivado_bin/xelab" "$top" --snapshot "${top}_v1" --debug all --timescale 1ns/1ps \
    > "${top}.elaborate.log" 2>&1 || { cat "${top}.elaborate.log"; exit 1; }
done
run_snapshot() {
  local snapshot="$1" label="$2" sentinel="$3"
  shift 3
  "$vivado_bin/xsim" "$snapshot" --tclbatch "$repo_root/sim/m20/run_all.tcl" \
    --wdb "$label.wdb" --log "$label.log" "$@" > "$label.console.log" 2>&1 \
    || { tail -n 100 "$label.console.log"; exit 1; }
  # XSIM may return zero after an HDL fatal: require a reached success marker.
  grep -q "$sentinel" "$label.log" \
    || { tail -n 100 "$label.log"; echo "Missing $sentinel" >&2; exit 1; }
}
run_snapshot tb_m20_isa_v1 isa M20_ISA_PASS
run_snapshot tb_m20_memory_v1 memory M20_MEMORY_PASS
for suite in instructions games; do
  run_snapshot tb_m20_cpu_v1 "$suite" M20_CPU_PASS --testplusarg "CASE_DIR=$output_root/$suite"
  "$python_bin" -B -m m20.rtl_regression compare --directory "$output_root/$suite" \
    > "$output_root/$suite/compare.log" 2>&1 || { cat "$output_root/$suite/compare.log"; exit 1; }
  cat "$output_root/$suite/compare.log"
done
"$python_bin" -B -m m20.rtl_regression summarize --output "$output_root" \
  > "$output_root/verification.log" 2>&1 || { cat "$output_root/verification.log"; exit 1; }
cat "$output_root/verification.log"
echo "M20_V1_REGRESSION_PASS output=$output_root"
