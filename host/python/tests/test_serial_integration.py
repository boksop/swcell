"""Linux pseudo-terminal integration; skipped when pyserial is not installed."""
import csv
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import tempfile
import time
import unittest

try:
    import serial
except ImportError:
    serial = None

SCRIPT = Path(__file__).resolve().parents[1] / 'swcell_capture.py'


@unittest.skipUnless(serial is not None and sys.platform.startswith('linux'), 'requires Linux + pyserial')
class SerialIntegrationTests(unittest.TestCase):
    def launch(self, directory):
        master, slave = os.openpty()
        self.addCleanup(os.close, master)
        self.addCleanup(os.close, slave)
        process = subprocess.Popen(
            [sys.executable, str(SCRIPT), '--port', os.ttyname(slave),
             '--output-root', directory, '--stop-on-complete'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(self.stop, process)
        ready, _, _ = select.select([process.stdout], [], [], 10)
        self.assertTrue(ready, 'serial capture did not start')
        self.assertIn('Saving to', process.stdout.readline())
        return master, process

    @staticmethod
    def stop(process):
        if process.poll() is None:
            process.kill()
        process.communicate()

    def test_fragmented_live_uart_to_csv(self):
        records = [dict(type='TEST_START', module='M11', test='L01'),
                   dict(type='TEST_RESULT', module='M11', test='L01', total_checks='0x1',
                        error_checks='0x0', q_errors='0x0', qm_errors='0x0', status='PASS'),
                   dict(type='TEST_COMPLETE', module='M11', tests='0x1', failed_tests='0x0', status='PASS')]
        wire = ('\n'.join(json.dumps(r) for r in records) + '\n').encode()
        with tempfile.TemporaryDirectory() as tmp:
            master, process = self.launch(tmp)
            os.write(master, wire[:19])
            time.sleep(0.02)
            os.write(master, wire[19:])
            _, stderr = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 0, stderr)
            directory = next(Path(tmp).iterdir())
            self.assertEqual((directory/'raw.jsonl').read_bytes(), wire)
            with (directory/'results.csv').open() as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['total_checks'], '1')
            self.assertTrue(json.loads((directory/'capture_summary.json').read_text())['complete_seen'])

    def test_ctrl_c_closes_live_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            master, process = self.launch(tmp)
            os.write(master, b'{"partial":')
            time.sleep(0.1)
            process.send_signal(signal.SIGINT)
            _, stderr = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 130, stderr)
            directory = next(Path(tmp).iterdir())
            self.assertEqual((directory/'raw.jsonl').read_bytes(), b'{"partial":')
            summary = json.loads((directory/'capture_summary.json').read_text())
            self.assertFalse(summary['complete_seen'])
            self.assertEqual(summary['invalid_lines'], 1)


if __name__ == '__main__':
    unittest.main()
