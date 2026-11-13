"""Reproduce the original cases and retain receiver evidence for a fresh review.

Standard library only. Each run requires a new output directory, so previous
evidence is never overwritten. These are local fixture tests, not live TIP tests.
"""
import concurrent.futures
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import sqlite3
import subprocess
import sys
import threading
import unittest

from baseline.revocation_demo import digest
from receiver import Receiver
from run import ROOT, scenario


def snapshot(path):
    """Read committed state through a separate read-only database connection."""
    with sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True) as db:
        integrity = db.execute('PRAGMA integrity_check').fetchone()[0]
        effects = db.execute('SELECT id, resource, value FROM effects ORDER BY id').fetchall()
        events = [dict(body=json.loads(body), hash=h) for body, h in
                  db.execute('SELECT body, hash FROM events ORDER BY seq')]
    previous = '0' * 64
    valid_chain = True
    for seq, event in enumerate(events, 1):
        body = event['body']
        valid_chain &= (body['seq'] == seq and body['previous_hash'] == previous
                        and digest(body) == event['hash'])
        previous = event['hash']
    return dict(integrity=integrity, effects=effects, events=events,
                event_chain_valid=valid_chain)


class ReceiverReview(unittest.TestCase):
    output = None
    observations = {}

    def setUp(self):
        self.path = self.output / (self._testMethodName + '.sqlite')
        self.r = Receiver(self.path)
        self.addCleanup(self.r.close)
        self.assertTrue(self.r.grant('root', 'agent', 'document'))
        self.assertTrue(self.r.enqueue('action', 'root', 'agent', 'document', 'changed'))

    def observe(self, **details):
        state = snapshot(self.path)
        self.observations[self._testMethodName] = dict(database=self.path.name,
                                                       **details, **state)
        self.assertEqual(state['integrity'], 'ok')
        self.assertTrue(state['event_chain_valid'])
        return state

    def test_acknowledgement_loss(self):
        # The caller discards the reply after delivery has returned. This models
        # an application-level lost acknowledgement, not a network fault injection.
        def caller():
            self.r.deliver('action')
            raise ConnectionError('simulated reply loss after committed delivery')

        with self.assertRaises(ConnectionError):
            caller()
        before = snapshot(self.path)
        self.assertEqual(before['effects'], [('action', 'document', 'changed')])
        with_receiver = Receiver(self.path)
        try:
            result = with_receiver.deliver('action')
        finally:
            with_receiver.close()
        state = self.observe(retry_result=result, fault='caller discards committed reply')
        self.assertEqual(result, 'ALREADY_COMMITTED')
        self.assertEqual(state['effects'], before['effects'])

    def test_committed_before_revocation(self):
        first = self.r.deliver('action')
        self.r.revoke('root')
        retry = self.r.deliver('action')
        state = self.observe(delivery_results=[first, retry])
        self.assertEqual([first, retry], ['COMMITTED', 'DENIED'])
        self.assertEqual(state['effects'], [('action', 'document', 'changed')])
        self.assertEqual([e['body']['kind'] for e in state['events']][-3:],
                         ['COMMITTED', 'REVOKE', 'DENIED'])

    def test_effect_rolls_back_when_recording_fails(self):
        original = self.r.record

        def fail_record(kind, **data):
            if kind == 'COMMITTED':
                raise RuntimeError('injected failure after effect insert')
            return original(kind, **data)

        self.r.record = fail_record
        try:
            with self.assertRaisesRegex(RuntimeError, 'injected failure'):
                self.r.deliver('action')
        finally:
            self.r.record = original
        before_retry = snapshot(self.path)
        self.assertEqual(before_retry['effects'], [])
        self.assertNotIn('COMMITTED', [e['body']['kind'] for e in before_retry['events']])
        result = self.r.deliver('action')
        state = self.observe(before_retry=before_retry, retry_result=result)
        self.assertEqual(result, 'COMMITTED')
        self.assertEqual(state['effects'], [('action', 'document', 'changed')])

    def test_revocation_lock_blocks_delivery(self):
        # A second connection attempts delivery while a revocation transaction
        # owns the write lock. timeout=0 makes contention deterministic without sleeps.
        worker = Receiver(self.path)
        try:
            worker.db.execute('PRAGMA busy_timeout=0')
            with self.r.transaction():
                self.r.db.execute("UPDATE grants SET revoked=1 WHERE id='root'")
                self.r.record('REVOKE', grant_id='root')
                with self.assertRaises(sqlite3.OperationalError) as error:
                    worker.deliver('action')
                self.assertEqual(error.exception.sqlite_errorcode, sqlite3.SQLITE_BUSY)
                self.assertEqual(snapshot(self.path)['effects'], [])
            result = worker.deliver('action')
        finally:
            worker.close()
        state = self.observe(while_locked='SQLITE_BUSY', after_revocation=result)
        self.assertEqual(result, 'DENIED')
        self.assertEqual(state['effects'], [])

    def test_concurrent_mixed_queue(self):
        self.assertTrue(self.r.grant('keep', 'agent', 'other-document'))
        # Both groups are queued before root is revoked. The unaffected group
        # must use exactly those original authorizations and payloads.
        for i in range(12):
            self.assertTrue(self.r.enqueue(f'deny-{i:02}', 'root', 'agent', 'document', str(i)))
            self.assertTrue(self.r.enqueue(f'keep-{i:02}', 'keep', 'agent', 'other-document', str(i)))
        self.r.revoke('root')
        self.assertEqual(snapshot(self.path)['effects'], [])
        release = threading.Event()

        def deliver(aid):
            if not release.wait(10):
                raise TimeoutError('worker start barrier')
            receiver = Receiver(self.path)
            try:
                return aid, receiver.deliver(aid)
            finally:
                receiver.close()

        actions = [f'{group}-{i:02}' for i in range(12)
                   for group in ('deny', 'keep') for attempt in range(2)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(deliver, aid) for aid in actions]
            release.set()
            results = [future.result(timeout=20) for future in futures]
        state = self.observe(workers=8, deliveries=len(results), delivery_results=results)
        self.assertEqual(state['effects'], [(f'keep-{i:02}', 'other-document', str(i))
                                           for i in range(12)])
        for i in range(12):
            self.assertEqual(sorted(v for k, v in results if k == f'deny-{i:02}'),
                             ['DENIED', 'DENIED'])
            self.assertEqual(sorted(v for k, v in results if k == f'keep-{i:02}'),
                             ['ALREADY_COMMITTED', 'COMMITTED'])


def main():
    output = Path(sys.argv[1]) if len(sys.argv) == 2 else ROOT / 'review-output'
    if len(sys.argv) > 2:
        raise SystemExit('Usage: python run_review.py [new-output-directory]')
    output.mkdir(parents=True, exist_ok=False)
    baseline = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                              cwd=ROOT / 'baseline', capture_output=True, text=True)
    (output / 'baseline.log').write_text(baseline.stdout + baseline.stderr)
    names = ['revocation', 'restart_retry', 'delegation', 'unrelated_change', 'duplicate_delivery']
    cases = [scenario(n, output / (n + '.sqlite')) for n in names]
    controls = [scenario(n, output / (m + '.sqlite'), m) for n, m in
                [('revocation', 'queue_only'), ('delegation', 'ignore_parent'),
                 ('unrelated_change', 'global_invalidation')]]
    ReceiverReview.output = output
    ReceiverReview.observations = {}
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(ReceiverReview))
    (output / 'review-tests.log').write_text(log.getvalue())
    all_passed = (baseline.returncode == 0 and all(c['passed'] for c in cases)
                  and all(not c['passed'] for c in controls)
                  and result.testsRun == 5 and result.wasSuccessful())
    sources = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(ROOT.rglob('*.py'))}
    report = dict(
        review_date='2026-11-12', executed_at_utc=datetime.now(timezone.utc).isoformat(),
        scope='Local SQLite receiving system; no live TIP or Harmonic integration',
        environment=dict(python=platform.python_version(), sqlite=sqlite3.sqlite_version,
                         platform=platform.platform()),
        passed=all_passed, baseline_exit_code=baseline.returncode,
        original_receiver_scenarios=cases, known_bad_controls=controls,
        additional_checks=dict(run=result.testsRun, failures=len(result.failures),
                               errors=len(result.errors), observations=ReceiverReview.observations),
        source_sha256=sources,
        database_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in sorted(output.glob('*.sqlite'))})
    (output / 'evidence.json').write_text(json.dumps(report, indent=2) + '\n')
    print(log.getvalue(), end='')
    print(f'Original baseline exit: {baseline.returncode}; receiver cases: '
          f'{sum(c["passed"] for c in cases)}/5; bad controls detected: '
          f'{sum(not c["passed"] for c in controls)}/3')
    print(f'{"PASS" if all_passed else "FAIL"}: {output / "evidence.json"}')
    return 0 if all_passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
