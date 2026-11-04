#!/usr/bin/env python3
"""Replay retained 79 witnesses without depending on ignored historical build data."""
import argparse
import hashlib
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESOURCES = ROOT / 'docs/m20/ff16_review_resources'


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(output):
    output = output.resolve()
    if output.exists() or ROOT / 'build/m20_300/v24_ff16' not in output.parents:
        raise ValueError('requires a fresh child of build/m20_300/v24_ff16')
    source = RESOURCES / 'cpu_witness_vectors.json'
    origin = load(RESOURCES / 'cpu_witness_vectors.origin.json')
    assert sha(source) == origin['source_sha256']
    assert sha(ROOT / 'rtl/m20/v21/generated/m20v21_cpu_core.netlist.json') == origin['frozen_netlist_sha256']
    vectors = load(source)
    assert [v['path_id'] for v in vectors] == list(range(79))
    output.mkdir(parents=True)
    (output / source.name).write_bytes(source.read_bytes())
    api = runpy.run_path(str(ROOT / 'tools/m20/ff16_review_xsim.py'))
    api['emit'](output)
    provenance = load(output / 'cone_provenance.json')
    assert provenance['generated_sv_sha256'] == load(RESOURCES / 'cone_provenance.json')['generated_sv_sha256']
    (output / 'versioned_input.json').write_text(json.dumps(origin, indent=2) + '\n')
    print('FF16_VERSIONED_WITNESSES_READY paths=79 ignored_build_dependency=NONE')


def check(output):
    api = runpy.run_path(str(ROOT / 'tools/m20/ff16_review_xsim.py'))
    api['check'](output)
    actual = load(output / 'cone_verification.json')
    expected = load(RESOURCES / 'cone_verification.json')
    # Full mismatch path IDs must agree, not merely a nonzero error count.
    assert actual == expected, 'retained positive/negative classifications changed'
    print('FF16_VERSIONED_REPLAY_PASS cases=632 observed_errors=131 physical=NOT_VERIFIED')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'check'))
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    {'prepare': prepare, 'check': check}[args.action](args.output)
