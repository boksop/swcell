"""Verify explicit repository relocations without rewriting frozen manifests."""
import hashlib
import json
import subprocess
from pathlib import Path


def verify_migration(root, relative, expected):
    root = Path(root).resolve()
    index = root / 'config/repository_migration_20261104.json'
    if not index.is_file():
        return None
    definition = json.loads(index.read_text())
    entry = definition['entries'].get(relative)
    if entry is None:
        return None
    if expected != entry['before_sha256']:
        raise ValueError('migration source SHA mismatch ' + relative)
    anchor = definition['baseline_commit']
    if len(anchor) != 40 or any(c not in '0123456789abcdef' for c in anchor):
        raise ValueError('invalid local migration anchor')
    old = subprocess.check_output(['git', '-C', str(root), 'show', anchor + ':' + relative])
    if hashlib.sha256(old).hexdigest() != expected:
        raise ValueError('historical Git blob SHA mismatch ' + relative)
    current = {}
    for target, digest in entry['current_files'].items():
        p = root / target
        if Path(target).is_absolute() or '..' in Path(target).parts or not p.resolve().is_relative_to(root) or not p.is_file():
            raise ValueError('missing/unsafe migration target ' + target)
        actual = hashlib.sha256(p.read_bytes()).hexdigest()
        if actual != digest:
            raise ValueError('migration target SHA mismatch ' + target)
        current[target] = actual
    if not current:
        raise ValueError('empty migration target ' + relative)
    return dict(status='VERIFIED_EXPLICIT_MIGRATION', historical_sha256=expected,
                baseline_commit=anchor, current_files=current,
                note='historical and current byte hashes are distinct; this is not a simulation PASS')
