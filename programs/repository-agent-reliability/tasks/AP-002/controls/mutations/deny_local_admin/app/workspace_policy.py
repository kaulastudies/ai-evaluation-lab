class WorkspacePolicy:
    def can_update(self, actor, document):
        if actor["workspace_id"] != document["workspace_id"]:
            return False
        return actor["role"] == "editor"
