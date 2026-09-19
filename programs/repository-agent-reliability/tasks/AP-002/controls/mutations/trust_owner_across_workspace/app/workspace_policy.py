class WorkspacePolicy:
    def can_update(self, actor, document):
        if actor["id"] == document["owner_id"]:
            return True
        if actor["workspace_id"] != document["workspace_id"]:
            return False
        return actor["role"] in {"editor", "admin"}
