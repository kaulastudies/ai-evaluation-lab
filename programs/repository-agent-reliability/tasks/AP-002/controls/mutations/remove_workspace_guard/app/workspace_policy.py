class WorkspacePolicy:
    def can_update(self, actor, document):
        return actor["role"] in {"editor", "admin"}
