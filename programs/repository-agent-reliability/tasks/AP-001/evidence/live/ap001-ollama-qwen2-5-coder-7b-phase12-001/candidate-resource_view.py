class ResourceView:
    """Tiny synthetic UI-state model with a stale-response bug."""

    def __init__(self):
        self.current_resource = None
        self.value = None
        self.pending_requests = {}

    def select_resource(self, resource, fetch):
        self.current_resource = resource

        def on_complete(value):
            if self.current_resource == resource:
                self.value = value

        if resource in self.pending_requests:
            self.pending_requests[resource] = on_complete
        else:
            fetch(resource, on_complete)

    def handle_request_completion(self, resource, value):
        if resource in self.pending_requests:
            on_complete = self.pending_requests.pop(resource)
            on_complete(value)
