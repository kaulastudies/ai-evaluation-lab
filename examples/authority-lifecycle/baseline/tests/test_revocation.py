import copy
import unittest
from revocation_demo import Gate, Delegation


class AuthorityRevocationTests(unittest.TestCase):
    def setUp(self):
        self.g = Gate()
        self.g.grant(Delegation('d1', 'owner', 'agent', ('read', 'write'), 100, 500))

    def test_01_valid_before_revocation_then_reject_after(self):
        self.assertEqual(self.g.action('d1', 'agent', 'write', 150)['payload']['decision'], 'ALLOW')
        self.g.revoke('d1', 200, 'owner')
        result = self.g.action('d1', 'agent', 'write', 201)
        self.assertEqual((result['payload']['decision'], result['payload']['reason']), ('REJECT', 'revoked'))
        self.assertTrue(self.g.verify())

    def test_02_revocation_issuer_cannot_be_spoofed(self):
        denied = self.g.revoke('d1', 200, 'stranger')
        self.assertEqual(denied['kind'], 'REJECT_REVOCATION')
        self.assertEqual(self.g.action('d1', 'agent', 'read', 201)['payload']['decision'], 'ALLOW')

    def test_03_old_grant_cannot_restore_post_revocation(self):
        self.g.revoke('d1', 200, 'owner')
        self.assertEqual(self.g.action('d1', 'agent', 'read', 300)['payload']['reason'], 'revoked')
        with self.assertRaises(ValueError):
            self.g.grant(Delegation('d1', 'owner', 'agent', ('read',), 300, 600))

    def test_04_scope_and_identity_restrictions_remain(self):
        self.assertEqual(self.g.action('d1', 'other-agent', 'read', 150)['payload']['reason'], 'wrong_agent')
        self.assertEqual(self.g.action('d1', 'agent', 'delete', 151)['payload']['reason'], 'scope_denied')
        self.assertEqual(self.g.action('d1', 'agent', 'read', 501)['payload']['reason'], 'outside_validity_window')

    def test_05_receipt_tampering_is_detected(self):
        self.g.revoke('d1', 200, 'owner')
        self.g.action('d1', 'agent', 'read', 201)
        self.assertTrue(self.g.verify())
        forged = copy.deepcopy(self.g.receipts)
        self.g.receipts[2]['payload']['decision'] = 'ALLOW'
        self.assertFalse(self.g.verify())
        self.g.receipts = forged
        self.assertTrue(self.g.verify())


if __name__ == '__main__':
    unittest.main()
  
