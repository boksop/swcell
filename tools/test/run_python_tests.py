#!/usr/bin/env python3
"""Run the frozen suite with explicit existing-output directory fixtures.

Two historical guard tests name output directories that happened to exist on
the original machine. Supply empty directories only when absent, and remove
only those same empty directories afterwards. No historical files are created,
copied, deleted or changed; original frozen tests remain untouched.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ROOT / 'host/python'))
    fixtures = (
        ROOT / 'build/m20_300/v24_ff16/small_r4',
        ROOT / 'build/m20_300/v23/session_20261103',
    )
    owned = []
    try:
        for path in fixtures:
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.mkdir()
                owned.append(path)
        print(f'PYTHON_GUARD_FIXTURES created_empty={len(owned)} historical_data_copied=0', flush=True)
        suite = unittest.defaultTestLoader.discover(str(ROOT / 'host/python/tests'))
        result = unittest.TextTestRunner(verbosity=1).run(suite)
        return 0 if result.wasSuccessful() else 1
    finally:
        for path in reversed(owned):
            try:
                path.rmdir()  # Refuses any unexpected file; never recursively deletes.
            except OSError:
                print(f'Guard fixture changed; left untouched: {path}', file=sys.stderr)


if __name__ == '__main__':
    raise SystemExit(main())
