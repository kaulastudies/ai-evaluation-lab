class ResourceView:
    """Tiny synthetic UI-state model with a stale-response bug."""

    def __init__(self):
        self.current_resource = None
        self.value = None
        self.requests = {}

    def select_resource(self, resource, fetch):
        self.current_resource = resource

        def on_complete(value):
            if self.current_resource == resource:
                self.value = value

        self.requests[resource] = on_complete
        fetch(resource, on_complete)

    def cancel_request(self, resource):
        self.requests.pop(resource, None)
