#!/usr/bin/env bash
# Isolated V2 baseline/shared XSIM three-way equivalence. Never modifies V1.
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
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
  [[ -x "$vivado_bin/$tool" ]] || { echo "Missing $tool; set M20_VIVADO_BIN" >&2; exit 127; }
done
output_root="${M20V2_OUTPUT_DIR:-$repo_root/build/m20_300/v2/regression}"
output_root="$(realpath -m "$output_root")"
case "$output_root/" in
  "$repo_root/build/m20_300/v1/"*) echo 'V2 must not write original V1 evidence' >&2; exit 2;;
esac
mkdir -p "$output_root"
output_root="$(cd "$output_root" && pwd)"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$repo_root/host/python${PYTHONPATH:+:$PYTHONPATH}"
"$vivado_bin/xvlog" --version > "$output_root/tool_version.log" 2>&1
grep -q '2026\.1' "$output_root/tool_version.log" \
  || { echo 'Select XSIM 2026.1 family using M20_VIVADO_BIN' >&2; exit 2; }
"$python_bin" -B -m m20.v2_verify prepare --output "$output_root" > "$output_root/prepare.log" 2>&1 \
  || { cat "$output_root/prepare.log"; exit 1; }
for variant in baseline shared; do
  run_dir="$output_root/$variant/xsim"
  mkdir -p "$run_dir"
  cd "$run_dir"
  sources=(
    "$repo_root/rtl/m20/m20_pkg.sv"
    "$repo_root/rtl/m20/m20_alu.sv"
    "$repo_root/rtl/m20/m20_decoder.sv"
    "$repo_root/rtl/m20/m20_control.sv"
    "$repo_root/rtl/m20/m20_pc.sv"
    "$repo_root/rtl/m20/m20_ar.sv"
    "$repo_root/rtl/m20/m20_cpu_core.sv"
    "$repo_root/rtl/m20/v2/swc_mux157.sv"
    "$repo_root/rtl/m20/v2/generated/$variant/m20v2_alu.sv"
    "$repo_root/rtl/m20/v2/generated/$variant/m20v2_decoder.sv"
    "$repo_root/rtl/m20/v2/generated/$variant/m20v2_cpu_core.sv"
    "$repo_root/sim/m20/rom_model.sv"
    "$repo_root/sim/m20/ram_model.sv"
    "$repo_root/sim/m20_v2/tb_swc_mux157.sv"
    "$repo_root/sim/m20_v2/tb_m20v2_isa.sv"
    "$repo_root/sim/m20_v2/tb_m20v2_memory.sv"
    "$repo_root/sim/m20_v2/tb_m20v2_cpu.sv"
  )
  "$vivado_bin/xvlog" --sv -i "$repo_root/sim/m20_v2" "${sources[@]}" > compile.log 2>&1 \
    || { tail -n 100 compile.log; exit 1; }
  for top in tb_swc_mux157 tb_m20v2_isa tb_m20v2_memory tb_m20v2_cpu; do
    "$vivado_bin/xelab" "$top" --snapshot "${top}_$variant" --debug all --timescale 1ns/1ps \
      > "$top.elaborate.log" 2>&1 || { tail -n 100 "$top.elaborate.log"; exit 1; }
  done
  run_snapshot() {
    local snapshot="$1" label="$2" sentinel="$3"
    shift 3
    "$vivado_bin/xsim" "$snapshot" --tclbatch "$repo_root/sim/m20_v2/run_all.tcl" \
      --wdb "$label.wdb" --log "$label.log" "$@" > "$label.console.log" 2>&1 \
      || { tail -n 100 "$label.console.log"; exit 1; }
    grep -q "$sentinel" "$label.log" \
      || { tail -n 100 "$label.log"; echo "Missing $sentinel" >&2; exit 1; }
  }
  run_snapshot "tb_swc_mux157_$variant" mux SWC_MUX157_PASS
  run_snapshot "tb_m20v2_isa_$variant" isa M20V2_ISA_PASS
  run_snapshot "tb_m20v2_memory_$variant" memory M20V2_MEMORY_PASS
  for suite in instructions games; do
    run_snapshot "tb_m20v2_cpu_$variant" "$suite" M20V2_CPU_PASS \
      --testplusarg "CASE_DIR=$output_root/$variant/$suite"
    "$python_bin" -B -m m20.v2_verify compare --directory "$output_root/$variant/$suite" \
      > "$output_root/$variant/$suite/compare.log" 2>&1 \
      || { cat "$output_root/$variant/$suite/compare.log"; exit 1; }
    cat "$output_root/$variant/$suite/compare.log"
  done
done
"$python_bin" -B -m m20.v2_verify summarize --output "$output_root" > "$output_root/verification.log" 2>&1 \
  || { cat "$output_root/verification.log"; exit 1; }
cat "$output_root/verification.log"
echo "M20_V2_REGRESSION_PASS output=$output_root"
