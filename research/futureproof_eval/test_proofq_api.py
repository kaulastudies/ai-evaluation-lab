import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from research.futureproof_eval.proofq_api import Handler

class ProofQApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = "http://127.0.0.1:%s" % cls.server.server_port
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
    def test_health(self):
        with urlopen(self.url + "/health") as r:
            self.assertEqual(json.load(r)["status"], "ok")
    def test_audit(self):
        payload = {"cases": [{"id": "zero", "theta_radians": 0, "ones": 0, "shots": 100}]}
        req = Request(self.url + "/v1/quantum/audit", json.dumps(payload).encode(), {"Content-Type": "application/json"})
        with urlopen(req) as r:
            self.assertEqual(json.load(r)["flagged"], 0)
    def test_invalid_json(self):
        req = Request(self.url + "/v1/quantum/audit", b"{oops", {"Content-Type": "application/json"})
        with self.assertRaises(HTTPError) as exc:
            urlopen(req)
        self.assertEqual(exc.exception.code, 400)
    def test_oversize(self):
        req = Request(self.url + "/v1/quantum/audit", b"x" * (128 * 1024 + 1))
        with self.assertRaises(HTTPError) as exc:
            urlopen(req)
        self.assertEqual(exc.exception.code, 413)

if __name__ == "__main__":
    unittest.main()
