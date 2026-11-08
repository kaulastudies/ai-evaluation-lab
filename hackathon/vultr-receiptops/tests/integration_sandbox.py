"""Run with Docker available. These are real containers, not Vultr/model evidence."""
import json
import unittest
from receiptops import audit, sandbox

class ContainerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not sandbox.available():
            raise RuntimeError('Docker/image unavailable: refusing to report skipped containment checks as a pass.')

    def test_fixed_containment_probes(self):
        result = sandbox.execute(sandbox.PROBE, audit.SAMPLE)
        self.assertEqual(result['exit_code'], 0, result)
        self.assertTrue(result['container_removed'], result)
        observed = json.loads(result['stdout'])
        expected = {'network_blocked', 'input_read_only', 'root_read_only', 'non_root', 'inference_key_absent', 'docker_socket_absent'}
        self.assertEqual(set(observed), expected)
        self.assertTrue(all(v is True for v in observed.values()), observed)

    def test_timeout_and_cleanup(self):
        result = sandbox.execute('while True: pass\n', audit.SAMPLE, timeout=2)
        self.assertTrue(result['timed_out'], result)
        self.assertTrue(result['container_removed'], result)

    def test_output_cap_and_cleanup(self):
        result = sandbox.execute('import os\nwhile True: os.write(1,b"x" * 4096)\n', audit.SAMPLE)
        self.assertTrue(result['output_limited'], result)
        self.assertLessEqual(len(result['stdout'].encode()), sandbox.POLICY['output_bytes'])
        self.assertTrue(result['container_removed'], result)

    def test_input_available_but_not_mutable(self):
        result = sandbox.execute('import pathlib\np=pathlib.Path("input.csv")\nprint(p.read_text(),end="")\n', audit.SAMPLE)
        self.assertEqual(result['exit_code'], 0, result)
        self.assertEqual(result['stdout'], audit.SAMPLE)
        self.assertTrue(result['container_removed'], result)

    def test_working_directory_disappears_with_container(self):
        first = sandbox.execute('from pathlib import Path\nPath("/tmp/receiptops-marker").write_text("private")\n', audit.SAMPLE)
        self.assertEqual(first['exit_code'], 0, first)
        second = sandbox.execute('from pathlib import Path\nprint(Path("/tmp/receiptops-marker").exists())\n', audit.SAMPLE)
        self.assertEqual(second['stdout'].strip(), 'False', second)
        self.assertTrue(first['container_removed'] and second['container_removed'])

if __name__ == '__main__':
    unittest.main(verbosity=2)
