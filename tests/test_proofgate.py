"""Integration checks for the local judge server's execution boundary."""
from contextlib import contextmanager
import http.client
import importlib.util
import json
import os
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch

DEMO = Path(__file__).resolve().parents[1] / 'hackathon/nebius-nvidia-rarb-demo'
sys.path.insert(0, str(DEMO))
import build_evidence
import serve


class EvidenceTests(unittest.TestCase):
    def test_bundle_matches_canonical_evidence_and_counts(self):
        actual = build_evidence.build()
        saved = json.loads((DEMO / 'evidence.json').read_text())
        self.assertEqual(actual, saved)
        counts = actual['summary']['counts']
        self.assertEqual(counts['attempts_total'], sum(counts[k] for k in ['verified_pass','verified_fail','hold']))
        self.assertTrue(actual['cases']['false-green']['manifest']['false_green'])
        self.assertTrue(actual['cases']['repair']['manifest']['repair_conversion'])
        self.assertEqual(actual['cases']['nemotron']['manifest']['provider'], 'nebius')
        self.assertIsNone(actual['cases']['hold']['candidate'])


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = serve.ThreadingHTTPServer(('127.0.0.1', 0), serve.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_port

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, method, path, body=None, headers=None):
        host = f'127.0.0.1:{self.port}'
        h = {'Host':host, 'Origin':f'http://{host}', 'X-ProofGate-Token':serve.TOKEN, 'Content-Type':'application/json'}
        h.update(headers or {})
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=30)
        conn.request(method,path,json.dumps(body) if body is not None else None,h)
        r = conn.getresponse(); data = r.read(); status = r.status; conn.close()
        return status, json.loads(data)

    def test_rejects_foreign_origin_and_dns_rebinding(self):
        for headers in [{'Origin':'https://untrusted.example'}, {'Host':'untrusted.example'}, {'X-ProofGate-Token':'wrong'}]:
            with self.subTest(headers=headers), patch.object(serve,'execute') as execute:
                status, _ = self.request('POST','/api/replay',{'case':'nemotron'},headers)
                self.assertEqual(status,403); execute.assert_not_called()

    def test_allowlist_rejects_arbitrary_paths_and_commands(self):
        with patch.object(serve,'execute') as execute:
            for value in ['../../README.md','python -c evil',None,[]]:
                status, _ = self.request('POST','/api/replay',{'case':value})
                self.assertEqual(status,400)
            execute.assert_not_called()
        status,_ = self.request('GET','/serve.py'); self.assertEqual(status,404)

    def test_missing_key_never_falls_back_to_stored_success(self):
        with patch.dict(os.environ,{},clear=True), patch.object(serve,'execute') as execute:
            status,data = self.request('POST','/api/run',{})
            self.assertEqual(status,503)
            self.assertIn('No model call',data['error']); execute.assert_not_called()

    def test_busy_rejects_duplicate_execution(self):
        serve.BUSY.acquire()
        try:
            status,_ = self.request('POST','/api/replay',{'case':'repair'})
            self.assertEqual(status,409)
        finally:
            serve.BUSY.release()

    def test_real_nemotron_evidence_replay(self):
        status,data = self.request('POST','/api/replay',{'case':'nemotron'})
        self.assertEqual(status,200)
        self.assertEqual(data['mode'],'executed_no_model_replay')
        self.assertEqual(data['report']['status'],'SOURCE_EXACT_REPLAY_VERIFIED')
        self.assertEqual(data['report']['replayed_verdict'],'VERIFIED_PASS')

    def test_real_repair_replay(self):
        status,data = self.request('POST','/api/replay',{'case':'repair'})
        self.assertEqual(status,200)
        self.assertEqual(data['report']['status'],'SOURCE_EXACT_REPAIR_REPLAY_VERIFIED')
        self.assertEqual(data['report']['replayed_verdict'],'VERIFIED_PASS')


if __name__ == '__main__':
    unittest.main()
