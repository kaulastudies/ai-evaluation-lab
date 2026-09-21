class ResourceView:
    """Tiny synthetic UI-state model with a stale-response bug."""

    def __init__(self):
        self.current_resource = None
        self.value = None

    def select_resource(self, resource, fetch):
        self.current_resource = resource

        def on_complete(value):
            if self.current_resource == resource:
                self.value = value

        fetch(resource, on_complete)
