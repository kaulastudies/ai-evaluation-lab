class ResourceView:
    def __init__(self):
        self.current_resource = None
        self.value = None
        self._generation = 0

    def select_resource(self, resource, fetch):
        self.current_resource = resource
        self._generation += 1
        request_generation = self._generation

        def on_complete(value):
            # Mutant: <= admits both current and stale generations.
            if request_generation <= self._generation:
                self.value = value

        fetch(resource, on_complete)
