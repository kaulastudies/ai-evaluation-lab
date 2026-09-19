import unittest

from app.workspace_policy import WorkspacePolicy


class PublicWorkspacePolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = WorkspacePolicy()
        self.document = {"workspace_id": "workspace-a", "owner_id": "user-1"}

    def test_same_workspace_editor_can_update(self):
        actor = {"id": "user-2", "workspace_id": "workspace-a", "role": "editor"}
        self.assertTrue(self.policy.can_update(actor, self.document))

    def test_same_workspace_admin_can_update(self):
        actor = {"id": "user-3", "workspace_id": "workspace-a", "role": "admin"}
        self.assertTrue(self.policy.can_update(actor, self.document))

    def test_same_workspace_viewer_cannot_update(self):
        actor = {"id": "user-4", "workspace_id": "workspace-a", "role": "viewer"}
        self.assertFalse(self.policy.can_update(actor, self.document))


if __name__ == "__main__":
    unittest.main()
