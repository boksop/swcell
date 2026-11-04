#!/usr/bin/env python3
"""Check changed/new documentation links, distinguishing pre-existing gaps."""
import argparse
import json
import re
import subprocess
from pathlib import Path
from project_catalog import ROOT

PATTERN = r'!?\[[^\]]*\]\(([^)]+)\)'


def resolve(parent, link):
    if re.match(r'\w+://', link) or link.startswith(('#', 'mailto:', 'plugin:', 'app:')):
        return None
    value = link.strip('<>').split('#')[0]
    return (parent / value).resolve() if value else None


def audit():
    definition = json.loads((ROOT / 'config/repository_migration_20261104.json').read_text())
    anchor = definition['baseline_commit']
    tracked = set(subprocess.check_output(['git', '-C', str(ROOT), 'ls-tree', '-r', '--name-only', anchor], text=True).splitlines())
    mapping = {old: next(iter(v['current_files'])) for old, v in definition['entries'].items()}
    mapping['README.md'] = 'README.md'
    pairs = {}
    for old, entry in definition['entries'].items():
        for current in entry['current_files']:
            if current.endswith('.md'):
                pairs[current] = old
    for folder in ('fpga', 'docs'):
        for p in (ROOT / folder).rglob('*.md'):
            name = str(p.relative_to(ROOT))
            if name not in tracked and not name.startswith('docs/history/'):
                pairs.setdefault(name, None)
    for name in ('TASK_PROGRESS.md', 'rtl/README.md', 'sim/README.md', 'host/README.md', 'software/README.md'):
        if (ROOT / name).exists():
            pairs.setdefault(name, name if name in tracked else None)
    errors, warnings, total = [], [], 0
    for current, old in sorted(pairs.items()):
        historical_missing = set()
        if old:
            text = subprocess.check_output(['git', '-C', str(ROOT), 'show', anchor + ':' + old], text=True)
            for link in re.findall(PATTERN, text):
                target = resolve((ROOT / old).parent, link)
                if target is None:
                    continue
                relative = str(target.relative_to(ROOT)) if target.is_relative_to(ROOT) else None
                known = relative in tracked or target.exists() or (relative and any(v.startswith(relative + '/') for v in tracked))
                if not known:
                    historical_missing.add((ROOT / mapping.get(relative, relative)).resolve() if relative else target)
        for link in re.findall(PATTERN, (ROOT / current).read_text()):
            target = resolve((ROOT / current).parent, link)
            if target is None:
                continue
            total += 1
            if not target.exists():
                row = dict(file=current, link=link, resolved=str(target))
                (warnings if target in historical_missing else errors).append(row)
    return dict(status='FAIL' if errors else 'PASS', documents_checked=len(pairs), local_links_checked=total,
                introduced_missing_links=errors, preexisting_missing_links=warnings,
                scope='local file existence only; URL reachability and Markdown anchors are not tested')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    result = audit()
    if args.output:
        dest = args.output.resolve()
        if dest.exists() or ROOT / 'build' not in dest.parents:
            p.error('use a fresh file under build/')
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
