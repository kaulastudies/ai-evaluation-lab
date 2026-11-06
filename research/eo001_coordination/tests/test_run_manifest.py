import unittest
from research.eo001_coordination.check_run_manifest import check, FIELDS


def complete():
    m = {k: 'a' * length for k, length in FIELDS.items()}
    m.update(schema='EO001-RUN-PLAN/0.1.0', context_serialization='synthetic fixture',
             host_configuration='synthetic fixture', output_naming='unique attempt IDs',
             cleanup_checks='synthetic fixture', generation_parameters={'temperature': 0},
             review_references={'lab': 'fixture only', 'evercraft': 'fixture only'},
             max_output_tokens=128, warmup_timeout_seconds=30, decision_timeout_seconds=15,
             max_decisions_per_case=6, warmup_requests=1,
             scenario_order=['none', 'ack_loss', 'lookup_outage', 'tamper'],
             stop_on_timeout=True, replace_failed_attempts=False)
    return m


class ManifestTests(unittest.TestCase):
    def test_complete_fields_never_authorize_execution(self):
        result = check(complete())
        self.assertEqual(result['state'], 'FIELDS_COMPLETE_REVIEW_REQUIRED')
        self.assertFalse(result['execution_authorized'])
        self.assertFalse(result['source_pins_or_review_authenticity_verified'])

    def test_missing_pin_is_named(self):
        m = complete()
        m['forge_adapter_commit'] = None
        self.assertIn('forge_adapter_commit', check(m)['unresolved_or_invalid_fields'])

    def test_timeout_extension_is_not_silent(self):
        m = complete()
        m['decision_timeout_seconds'] = 30
        self.assertIn('decision_timeout_seconds', check(m)['unresolved_or_invalid_fields'])

    def test_failure_replacement_is_rejected(self):
        m = complete()
        m['replace_failed_attempts'] = True
        self.assertIn('failure_retention_policy', check(m)['unresolved_or_invalid_fields'])

    def test_boolean_budget_is_rejected(self):
        m = complete()
        m['max_output_tokens'] = True
        self.assertIn('max_output_tokens', check(m)['unresolved_or_invalid_fields'])

    def test_hash_changes_with_protocol(self):
        m = complete()
        before = check(m)['manifest_sha256']
        m['generation_parameters']['temperature'] = 0.5
        self.assertNotEqual(before, check(m)['manifest_sha256'])
