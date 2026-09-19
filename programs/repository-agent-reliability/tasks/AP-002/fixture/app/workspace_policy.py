class WorkspacePolicy:
    """Synthetic workspace-scoped update authorization policy."""

    def can_update(self, actor, document):
        # BUG: privileged role is treated as global instead of workspace-scoped.
        if actor["role"] in {"editor", "admin"}:
            return True

        return False
