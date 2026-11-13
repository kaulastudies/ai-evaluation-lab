"""Contract checks for the exact Python engine used by the browser demo."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('demo_engine', Path(__file__).parent / 'web' / 'engine.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


class BrowserEngineTests(unittest.TestCase):
    def finish(self, case, broken=False):
        demo = engine.Demo(case, broken)
        self.addCleanup(demo.close)
        while not demo.state()['done']:
            demo.advance()
        return demo.state()

    def test_all_eight_correct_scenarios(self):
        for name in engine.CASES:
            with self.subTest(case=name):
                self.assertTrue(self.finish(name)['contract_met'])

    def test_three_broken_controls_violate_the_contract(self):
        for name in ('revocation', 'delegation', 'continuation'):
            with self.subTest(case=name):
                self.assertFalse(self.finish(name, True)['contract_met'])

    def test_same_queued_authorization_survives_unrelated_revocation(self):
        state = self.finish('continuation')
        queue_index = next(i for i,h in enumerate(state['history']) if h['operation']=='queue')
        kinds_after_queue = [h['operation'] for h in state['history'][queue_index+1:]]
        self.assertEqual(kinds_after_queue, ['revoke', 'deliver'])
        self.assertEqual(state['queue'][0][1], 'grant-A')
        self.assertEqual(state['effects'], [('action-A','document-A','approved-change')])

    def test_rollback_snapshot_precedes_successful_retry(self):
        state = self.finish('rollback')
        failed = next(h for h in state['history'] if h['operation']=='rollback')
        self.assertEqual(failed['effects'], [])
        self.assertNotIn('COMMITTED', [e['body']['kind'] for e in failed['events']])
        self.assertEqual(len(state['effects']), 1)

    def test_original_effect_is_not_erased_by_revocation(self):
        state = self.finish('committed')
        self.assertEqual(state['delivery_results'], ['COMMITTED', 'DENIED'])
        self.assertEqual(len(state['effects']), 1)

    def test_reset_isolates_scenarios(self):
        engine.command_json('{"action":"reset","case":"duplicate"}')
        engine.command_json('{"action":"run"}')
        import json
        state=json.loads(engine.command_json('{"action":"reset","case":"revocation"}'))
        self.assertEqual(state['effects'], [])
        self.assertEqual(state['events'], [])
        engine.active.close()
        engine.active=None


if __name__ == '__main__':
    unittest.main()
