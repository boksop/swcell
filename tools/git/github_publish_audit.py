#!/usr/bin/env python3
"""Read-only publication preflight: all reachable Git objects and candidate files.

No network, Git mutations or secret values in reports. Pattern matching is a
best-effort screen, not proof that no possible credential or copyright exists.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
MIB = 1024 * 1024
PATTERNS = {
    'private_key': rb'-----BEGIN(?: RSA| EC| DSA| OPENSSH| ENCRYPTED)? PRIVATE KEY-----',
    'github_classic_token': rb'\bgh[pousr]_[A-Za-z0-9]{30,}\b',
    'github_fine_grained_token': rb'\bgithub_pat_[A-Za-z0-9_]{40,}\b',
    'aws_access_key': rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'openai_key_like': rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{30,}\b',
    'slack_token_like': rb'\bxox[baprs]-[A-Za-z0-9-]{20,}\b',
    'credential_assignment': rb'''(?im)\b(?:password|passwd|api[_-]?key|access[_-]?token|client[_-]?secret)\b\s*[:=]\s*['"][^'"\r\n]{12,}['"]''',
    'credential_in_url': rb'https?://[^\s/:@]+:[^\s/@]{4,}@',
}
SENSITIVE_NAME = re.compile(r'(^|/)(?:id_(?:rsa|ed25519)|credentials|hosts\.yml|\.env(?:\..*)?)$|\.(?:pem|p12|pfx|key)$', re.I)
CACHE_NAME = re.compile(r'(^|/)(?:build|\.venv[^/]*|\.Xil|xsim\.dir|\.cache)(/|$)|\.(?:wdb|fsdb|fst|dcp|bit|ltx|jou|pb)$')


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])


def findings(data):
    result = []
    for kind, pattern in PATTERNS.items():
        for match in re.finditer(pattern, data):
            result.append(dict(kind=kind, line=data.count(b'\n', 0, match.start()) + 1,
                               value_sha256=hashlib.sha256(match.group()).hexdigest()))
    return result


def audit(root):
    commits = git(root, 'rev-list', '--all').decode().splitlines()
    paths = defaultdict(set)
    modes = defaultdict(set)
    for commit in commits:
        for entry in git(root, 'ls-tree', '-rz', commit).split(b'\0'):
            if not entry:
                continue
            header, name = entry.split(b'\t', 1)
            mode, kind, oid = header.decode().split()
            path = os.fsdecode(name)
            paths[oid].add(path)
            modes[path].add(mode)
    objects = set()
    for row in git(root, 'rev-list', '--objects', '--all').splitlines():
        objects.add(row.split(b' ', 1)[0].decode())
    result = dict(schema_version=1, head=git(root, 'rev-parse', 'HEAD').decode().strip(),
                  commit_count=len(commits), tags=git(root, 'tag', '--list').decode().splitlines(),
                  scope='Every reachable commit/tag/blob plus tracked and unignored candidate files; ignored build/results are not upload candidates',
                  secret_findings=[], sensitive_names=[], large_files=[], cache_files=[],
                  third_party_notices=[], lfs_pointers=[], symlink_warnings=[], errors=[])
    counts = Counter()
    largest = []
    process = subprocess.Popen(['git', '-C', str(root), 'cat-file', '--batch'],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        for oid in sorted(objects):
            process.stdin.write((oid + '\n').encode()); process.stdin.flush()
            header = process.stdout.readline().decode().split()
            if len(header) != 3:
                raise ValueError('Cannot inspect Git object ' + oid)
            _, kind, size = header; size = int(size)
            data = process.stdout.read(size)
            if len(data) != size or process.stdout.read(1) != b'\n':
                raise ValueError('Truncated Git object ' + oid)
            counts[kind] += 1
            if kind not in ('blob', 'commit', 'tag'):
                continue
            names = sorted(paths[oid]) if kind == 'blob' else [kind + ':' + oid]
            for hit in findings(data):
                result['secret_findings'].append(dict(scope='history', object=oid, paths=names, **hit))
            if kind == 'blob':
                largest.append(dict(scope='history', object=oid, bytes=size, paths=names))
                if size > 50 * MIB:
                    result['large_files'].append(largest[-1])
                for name in names:
                    if SENSITIVE_NAME.search(name):
                        result['sensitive_names'].append(dict(scope='history', path=name, object=oid))
                    if CACHE_NAME.search(name):
                        result['cache_files'].append(dict(scope='history', path=name, object=oid, bytes=size))
                if data.startswith(b'version https://git-lfs.github.com/spec/v1'):
                    result['lfs_pointers'].append(dict(scope='history', paths=names))
                if re.search(rb'(?im)^.{0,15}(?:copyright\s+(?:\(c\)\s*)?\d|SPDX-License-Identifier:|all rights reserved)', data):
                    result['third_party_notices'].append(dict(scope='history', object=oid, paths=names))
    finally:
        process.stdin.close(); process.stdout.close(); process.wait()
    candidates = sorted(set(os.fsdecode(n) for n in git(root, 'ls-files', '-c', '-o', '--exclude-standard', '-z').split(b'\0') if n))
    current = []
    for name in candidates:
        p = root / name
        if p.is_symlink():
            data = os.fsencode(os.readlink(p))
            if not p.exists() or not p.resolve().is_relative_to(root):
                result['symlink_warnings'].append(name)
        elif p.is_file():
            data = p.read_bytes()
        else:
            result['errors'].append('Missing candidate ' + name); continue
        current.append(dict(path=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
        for hit in findings(data):
            result['secret_findings'].append(dict(scope='candidate', paths=[name], **hit))
        if re.search(rb'(?im)^.{0,15}(?:copyright\s+(?:\(c\)\s*)?\d|SPDX-License-Identifier:|all rights reserved)', data):
            result['third_party_notices'].append(dict(scope='candidate', paths=[name]))
        if data.startswith(b'version https://git-lfs.github.com/spec/v1'):
            result['lfs_pointers'].append(dict(scope='candidate', paths=[name]))
        if SENSITIVE_NAME.search(name):
            result['sensitive_names'].append(dict(scope='candidate', path=name))
        if CACHE_NAME.search(name):
            result['cache_files'].append(dict(scope='candidate', path=name, bytes=len(data)))
        if len(data) > 50 * MIB:
            result['large_files'].append(dict(scope='candidate', paths=[name], bytes=len(data)))
    if result['secret_findings'] or result['sensitive_names']:
        result['errors'].append('Credentials or sensitive names require manual review before upload')
    if any(row['bytes'] > 100 * MIB for row in result['large_files']):
        result['errors'].append('Object exceeds the GitHub 100MiB file limit; do not rewrite history automatically')
    if result['cache_files']:
        result['errors'].append('Tracked/candidate tool caches require review')
    if result['symlink_warnings']:
        result['errors'].append('Broken/external symlinks require review')
    result.update(object_counts=dict(counts), history_largest_blobs=sorted(largest, key=lambda x: x['bytes'], reverse=True)[:15],
                  candidate_count=len(current), candidate_bytes=sum(x['bytes'] for x in current), candidate_files=current,
                  submodule_paths=sorted(p for p, values in modes.items() if '160000' in values),
                  status='PASS' if not result['errors'] else 'REVIEW_REQUIRED',
                  limitations='Known token/key/URL patterns and names only; not a universal secret detector or legal review. No secret value is printed.')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); destination = args.output.resolve()
    if destination.exists():
        parser.error('Use a fresh audit output directory')
    result = audit(args.root.resolve())
    destination.mkdir(parents=True)
    (destination / 'publication_audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    summary = {k: v for k, v in result.items() if k not in ('candidate_files',)}
    (destination / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'commit_count', 'object_counts', 'candidate_count', 'errors')}, ensure_ascii=False))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
