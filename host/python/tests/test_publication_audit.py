"""Publication gate examples use constructed fake values, never credentials."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location('publication_audit', ROOT / 'tools/git/github_publish_audit.py')
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class PublicationAuditTests(unittest.TestCase):
    def test_token_finding_is_redacted(self):
        fake = b'gh' + b'p_' + b'A' * 36
        findings = AUDIT.findings(b'prefix\n' + fake + b'\n')
        self.assertEqual(len(findings), 1)
        self.assertEqual((findings[0]['kind'], findings[0]['line']), ('github_classic_token', 2))
        self.assertNotIn(fake.decode(), json.dumps(findings))

    def test_key_and_quoted_credential_are_detected(self):
        fake_key = b'-----BEGIN' + b' OPENSSH PRIVATE KEY-----'
        fake_assignment = b'pass' + b'word = "' + b'not-a-real-credential' + b'"'
        kinds = {row['kind'] for row in AUDIT.findings(fake_key + b'\n' + fake_assignment)}
        self.assertEqual(kinds, {'private_key', 'credential_assignment'})

    def test_normal_board_metadata_is_not_a_secret(self):
        self.assertEqual(AUDIT.findings(b'UART=/dev/ttyUSB1\nCLK_HZ=50000000\nHOST=192.168.2.34\n'), [])

    def test_cache_and_reference_rom_are_distinguished(self):
        self.assertIsNotNone(AUDIT.CACHE_NAME.search('project/.cache/example'))
        self.assertIsNotNone(AUDIT.CACHE_NAME.search('old/test.bit'))
        self.assertIsNone(AUDIT.CACHE_NAME.search('software/m20_300/rom/pong.bin'))
        self.assertIsNotNone(AUDIT.SENSITIVE_NAME.search('private/id_ed25519'))
