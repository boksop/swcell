#!/usr/bin/env python3
"""Copy selected small V3 evidence unchanged; never overwrite originals/archives."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]


def archive(destination):
    if destination.exists():
        raise ValueError('Use a fresh archive directory')
    selected = []

    def add(source, target):
        source = ROOT / source
        if not source.is_file():
            raise FileNotFoundError(source)
        if source.stat().st_size > 2 * 1024 * 1024:
            raise ValueError('Small-evidence limit exceeded: ' + str(source))
        selected.append((source, Path(target)))

    final = 'build/fpga/m20/cpu_validation/snake_shuffled_boot_r1/'
    for name in ('timing.rpt', 'utilization.rpt', 'drc.rpt', 'cdc.rpt', 'check_timing.rpt',
                 'ram.rpt', 'io.rpt', 'source_sha256.txt', 'software_profile.txt', 'pre_program_verification.json',
                 'route_audit/counts.json', 'route_audit/mux_mapping.csv', 'route_audit/cpu_storage_ff.txt'):
        add(final + name, 'fpga_f06/' + name)
    for name in ('drc.rpt', 'timing.rpt', 'utilization.rpt'):
        add('build/fpga/m20/cpu_validation/strict_r2/' + name, 'strict_mux_blocked/' + name)
    add('build/fpga/m20/cpu_validation/FUNCTIONAL_STORAGE/timing.rpt', 'early_functional_timing_failure/timing.rpt')
    for suite in ('instructions', 'games'):
        for name in ('comparison.json', 'three_way_comparison.json'):
            add('build/sim/m20_v3/core_r2/' + suite + '/' + name, 'simulation/core/' + suite + '/' + name)
    for test in ('isa', 'datapath', 'illegal', 'memory', 'instructions', 'games'):
        add('build/sim/m20_v3/core_r2/xsim/' + test + '.log', 'simulation/core/' + test + '.txt')
    for directory in ('boot_entry_r1', 'boot_entry_r2', 'system_r11', 'shuffled_r1', 'inputs_r1'):
        source = ROOT / 'build/sim/m20_v3' / directory
        log = source / ('xsim/simulation.log' if directory == 'shuffled_r1' else 'simulation.log')
        if not log.is_file() and directory == 'inputs_r1':
            log = source / 'simulation.log'
        add(str(log.relative_to(ROOT)), 'simulation/' + directory + '/simulation.txt')
    add('build/sim/m20_v3/system_r11/frame_snapshots.verification.json', 'simulation/system_r11/frame_oracle.json')
    for name in ('comparison.json', 'three_way_comparison.json'):
        add('build/sim/m20_v3/shuffled_r1/' + name, 'simulation/shuffled_r1/' + name)
    add('build/m20_v3_python_boot_entry_r1.log', 'simulation/python_164.txt')
    add('build/m20_v3_program_boot_entry_r1.log', 'fpga_f06/jtag_program.txt')
    for run in sorted((ROOT / 'results/M20_V3').iterdir()):
        if run.is_dir():
            for p in sorted(run.iterdir()):
                if p.is_file() and p.suffix in ('.json', '.jsonl', '.csv', '.memh'):
                    add(str(p.relative_to(ROOT)), str(Path('hardware') / run.name / p.name))
    # Resolve every source before creating output: missing evidence never yields
    # a partially populated archive presented as complete.
    destination.mkdir(parents=True)
    rows = []
    for source, relative in selected:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise ValueError('Copy checksum mismatch')
        rows.append(dict(source=str(source.relative_to(ROOT)), copy=str(relative),
                         bytes=source.stat().st_size, sha256=digest))
    manifest = dict(schema_version=1, date='2026-11-04', selection='V3 small hardware data, final FPGA reports, positive/negative digital evidence',
                    copy_policy='Exact bytes; originals kept in build/results; .log copies named .txt explicitly; no bit/DCP/cache/large waves',
                    files=rows, count=len(rows), bytes=sum(r['bytes'] for r in rows),
                    limits='Evidence archive, not a source snapshot or replacement for independent test execution. Manifest excludes itself.')
    (destination / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print('V3_EVIDENCE_ARCHIVE_PASS', len(rows), manifest['bytes'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    archive(parser.parse_args().output.resolve())
