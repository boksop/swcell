#!/usr/bin/env python3
"""Read-only SwCell FPGA project catalog. Never builds or connects to hardware."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read_projects(root=ROOT):
    return [(p, json.loads(p.read_text())) for p in sorted((root / 'fpga/projects').glob('**/project.json'))]


def check(root=ROOT):
    errors = []
    ids = set()
    for path, project in read_projects(root):
        name = project.get('id')
        if not name or name in ids:
            errors.append(f'{path}: missing/duplicate project id')
        ids.add(name)
        status = project.get('status')
        if status not in ('IMPLEMENTED', 'PLANNED'):
            errors.append(f'{name}: unknown project status')
        if status == 'IMPLEMENTED' and not project.get('build_script'):
            errors.append(f'{name}: implemented project needs build_script')
        if status == 'PLANNED' and not project.get('todos'):
            errors.append(f'{name}: planned project needs explicit todos')
        paths = [project.get('board_profile'), project.get('build_script'), project.get('readme')]
        paths += project.get('constraints', []) + project.get('references', [])
        for value in filter(None, paths):
            target = root / value
            if Path(value).is_absolute() or '..' in Path(value).parts or not target.resolve().is_relative_to(root.resolve()) or not target.is_file():
                errors.append(f'{name}: missing/unsafe file {value}')
        for pattern in project.get('source_globs', []):
            if Path(pattern).is_absolute() or '..' in Path(pattern).parts or not any(p.is_file() for p in root.glob(pattern)):
                errors.append(f'{name}: missing/unsafe source glob {pattern}')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('list', 'show', 'check'))
    parser.add_argument('project', nargs='?')
    args = parser.parse_args()
    projects = read_projects()
    if args.command == 'check':
        errors = check()
        for error in errors:
            print('ERROR:', error)
        if errors:
            return 1
        print(f'PROJECT_CATALOG_PASS projects={len(projects)}; PLANNED entries do not imply build/hardware readiness')
    elif args.command == 'list':
        for _, p in projects:
            print(f'{p["id"]:30} {p["status"]:12} {p["description"]}')
    else:
        selected = [p for _, p in projects if p['id'] == args.project]
        if len(selected) != 1:
            parser.error('provide an exact project id from list')
        print(json.dumps(selected[0], ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
