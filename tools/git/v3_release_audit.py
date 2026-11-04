#!/usr/bin/env python3
"""Read-only V3 source/ROM regeneration and archived-evidence verification."""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def inspect(root):
    manifest = json.loads((root / 'docs/m20/M20_V3_SOURCE_MANIFEST.json').read_text())
    for name, digest in manifest['files'].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
    sys.path.insert(0, str(root / 'host/python'))
    generated = 0
    with tempfile.TemporaryDirectory(prefix='swcell-v3-audit-') as temp:
        for generator, checked, names in (
            ('v3_generate', 'rtl/modules/m20/v3/generated', ('m20v3_cpu_core.sv', 'binding_manifest.json', 'games.json', 'm20_v3_game_pkg.sv', 'pong.memh', 'snake.memh')),
            ('v3_snake_shuffled', 'software/m20_300/variants/snake_shuffled_v0_1', ('snake_shuffled.asm', 'snake_shuffled.memh', 'food_table.json', 'manifest.json')),
        ):
            spec = importlib.util.spec_from_file_location(generator, root / ('tools/m20/' + generator + '.py'))
            module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
            destination = Path(temp) / generator
            with contextlib.redirect_stdout(io.StringIO()):
                module.generate(destination)
            for name in names:
                assert (destination / name).read_bytes() == (root / checked / name).read_bytes(), name
                generated += 1
    from m20.v21_audit import audit
    from m20.ff16_structure import audit as audit_clock
    counts = audit(root / 'rtl/m20/v21/generated/m20v21_cpu_core.sv', root / 'rtl/m20/v21/generated/m20v21_cpu_core.netlist.json', root / 'rtl/m20/v21/swc_mux157.sv')
    assert (counts['combinational_mux'], counts['ff_bits'], counts['full_equivalent']) == (477, 33, 543)
    clock = audit_clock(root / 'rtl/m20/v24_ff16')
    archive = root / 'docs/evidence/m20_v3'
    evidence = json.loads((archive / 'manifest.json').read_text())
    for row in evidence['files']:
        assert hashlib.sha256((archive / row['copy']).read_bytes()).hexdigest() == row['sha256'], row['copy']
    return dict(status='PASS', commit=subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(),
                source_files=len(manifest['files']), regenerated_files=generated, combinational_mux=477, cpu_state_bits=33,
                physical_cpu_equivalent=543, clock_audit=clock, archived_evidence_files=len(evidence['files']),
                limits='Source/evidence restoration; Python, XSIM, synthesis and hardware are separate checks')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Use a fresh report file')
    result = inspect(args.root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print('V3_RELEASE_AUDIT_PASS', result['source_files'], 'sources', result['regenerated_files'], 'regenerated files')
