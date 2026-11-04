"""Migration contracts: catalog, pins/config and frozen-fingerprint rejection."""
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


class RepositoryLayoutTests(unittest.TestCase):
    def test_catalog_has_independent_projects_and_implemented_cpu(self):
        catalog = module('swc_catalog', 'tools/fpga/project_catalog.py')
        self.assertEqual(catalog.check(ROOT), [])
        projects = {p['id']: p for _, p in catalog.read_projects(ROOT)}
        self.assertTrue({'m11/functional', 'm11/performance', 'diagnostics/uart_loopback', 'diagnostics/uart_pin_id', 'm20/cpu_validation'} <= set(projects))
        self.assertEqual(projects['m20/cpu_validation']['status'], 'IMPLEMENTED')
        self.assertEqual(projects['m20/cpu_validation']['build_script'], 'fpga/projects/m20/cpu_validation/scripts/build.tcl')
        self.assertIn('rtl/modules/m20/v3/generated/*.sv', projects['m20/cpu_validation']['source_globs'])
        self.assertNotEqual(projects['m11/functional']['build_script'], projects['m11/performance']['build_script'])

    def test_split_constraints_preserve_all_original_pin_values(self):
        definition = json.loads((ROOT / 'config/repository_migration_20261104.json').read_text())
        old = subprocess.check_output(['git', '-C', str(ROOT), 'show', definition['baseline_commit'] + ':fpga/xc7k325t/constraints/board_50mhz.xdc'], text=True)
        files = ['fpga/boards/swcell_k325t/constraints/base_io.xdc', 'fpga/projects/m11/common/constraints/m11_io.xdc']
        pattern = r'set_property PACKAGE_PIN (\w+) \[get_ports (\w+)\]'
        old_pins = dict((port, pin) for pin, port in re.findall(pattern, old))
        pairs = [pair for name in files for pair in re.findall(pattern, (ROOT / name).read_text())]
        self.assertEqual(len(pairs), 13)
        self.assertEqual(len(set(port for _, port in pairs)), 13)
        self.assertEqual(old_pins, {port: pin for pin, port in pairs})
        self.assertEqual(len(re.findall(pattern, (ROOT / files[1]).read_text())), 7)

    def test_all_retained_m11_port_projects_load_all_thirteen_pins(self):
        catalog = module('swc_catalog_ports', 'tools/fpga/project_catalog.py')
        projects = {p['id']: p for _, p in catalog.read_projects(ROOT)}
        pattern = r'set_property PACKAGE_PIN (\w+) \[get_ports (\w+)\]'
        for name in ('m11/functional', 'm11/performance', 'diagnostics/uart_loopback'):
            pairs = [pair for path in projects[name]['constraints'] for pair in re.findall(pattern, (ROOT / path).read_text())]
            self.assertEqual(len(pairs), 13, name)
            self.assertEqual(len(set(port for _, port in pairs)), 13, name)

    def test_board_profile_split_preserves_old_parameters(self):
        definition = json.loads((ROOT / 'config/repository_migration_20261104.json').read_text())
        old = subprocess.check_output(['git', '-C', str(ROOT), 'show', definition['baseline_commit'] + ':fpga/xc7k325t/config/board_50mhz.tcl'], text=True)
        dump = '\nforeach k [lsort [array names swc]] {puts "$k=$swc($k)"}\n'
        def evaluate(text):
            out = subprocess.run(['tclsh'], input=text + dump, text=True, capture_output=True, check=True)
            return dict(line.split('=', 1) for line in out.stdout.splitlines())
        before = evaluate(old)
        after = evaluate('source {' + str(ROOT / 'fpga/projects/m11/functional/config/default.tcl') + '}')
        before.pop('board_xdc')
        self.assertEqual(before, {key: after[key] for key in before})
        self.assertTrue(Path(after['board_xdc']).is_file())
        self.assertTrue(Path(after['module_xdc']).is_file())

    def test_frozen_manifest_migration_rejects_incorrect_expected_hash(self):
        support = module('swc_layout_paths', 'tools/git/layout_paths.py')
        index = json.loads((ROOT / 'config/repository_migration_20261104.json').read_text())
        key = 'fpga/xc7k325t/rtl/swcell_fpga_top.sv'
        entry = index['entries'][key]
        result = support.verify_migration(ROOT, key, entry['before_sha256'])
        self.assertEqual(result['status'], 'VERIFIED_EXPLICIT_MIGRATION')
        with self.assertRaises(ValueError):
            support.verify_migration(ROOT, key, '0' * 64)
