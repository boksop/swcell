#!/usr/bin/env python3
"""Read-only layout/lineage/reference audit; optional fresh output directory."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
from project_catalog import ROOT, check as check_catalog


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit():
    definition = json.loads((ROOT / 'config/repository_migration_20261104.json').read_text())
    spec = importlib.util.spec_from_file_location('swc_lineage', ROOT / 'tools/git/layout_paths.py')
    lineage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lineage)
    errors = check_catalog(ROOT)
    for relative, entry in definition['entries'].items():
        try:
            lineage.verify_migration(ROOT, relative, entry['before_sha256'])
        except Exception as error:
            errors.append(str(error))
    for relative, expected in definition['immutable_historical_files'].items():
        if not (ROOT / relative).is_file() or digest(ROOT / relative) != expected:
            errors.append('immutable evidence changed: ' + relative)
    for record in definition['baseline_tag_objects']:
        name, obj, target = record.split('|')
        if subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', name], text=True).strip() != obj:
            errors.append('original tag moved: ' + name)
    # Independently prove that frozen logical sources and moved board RTL did not change.
    tracked = subprocess.check_output(['git', '-C', str(ROOT), 'ls-tree', '-r', '--name-only', definition['baseline_commit']], text=True).splitlines()
    unchanged = 0
    for relative in tracked:
        if not (relative.startswith(tuple(definition['logical_sources_unchanged_prefixes'])) or relative.endswith('.sv')):
            continue
        old = subprocess.check_output(['git', '-C', str(ROOT), 'show', definition['baseline_commit'] + ':' + relative])
        mapping = definition['entries'].get(relative)
        targets = mapping['current_files'] if mapping else {relative: None}
        primary = next(iter(targets))
        if not (ROOT / primary).is_file() or (ROOT / primary).read_bytes() != old:
            errors.append('logical source bytes changed: ' + relative)
        unchanged += 1
    # File references, not fabric/STA correctness: only literal repository source paths.
    references = 0
    for script in sorted((ROOT / 'fpga').glob('**/*.tcl')):
        code = script.read_text()
        complete = subprocess.run(['tclsh'], input='set f [open {' + str(script) + '} r];set s [read $f];close $f;puts [info complete $s]\n', text=True, capture_output=True, check=True)
        if complete.stdout.strip() != '1':
            errors.append('incomplete Tcl: ' + str(script.relative_to(ROOT)))
        for tokens in re.findall(r'\[file join \$root ([^\[\]\n]+)\]', code):
            parts = tokens.split()
            if any('$' in part for part in parts) or parts[0] in ('build', '.venv') or 'board.local' in parts[-1]:
                continue
            pattern = '/'.join(parts)
            matches = list(ROOT.glob(pattern))
            if not any(p.exists() for p in matches):
                errors.append(f'{script.relative_to(ROOT)} missing literal reference: {pattern}')
            references += 1
    from datetime import datetime
    return dict(status='FAIL' if errors else 'PASS',date=datetime.now().astimezone().isoformat(),
                baseline_commit=definition['baseline_commit'],migration_entries=len(definition['entries']),
                immutable_evidence_files=len(definition['immutable_historical_files']),unchanged_logical_sources=unchanged,
                literal_tcl_references=references,original_tag_objects_unchanged=not any('tag moved' in x for x in errors),
                errors=errors,limits='path/source/lineage checks only; not synthesis, STA or hardware validation')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    result = audit()
    if args.output:
        target = args.output.resolve()
        if target.exists() or ROOT / 'build' not in target.parents:
            p.error('use a fresh report directory under build/')
        target.mkdir(parents=True)
        (target / 'layout_audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
