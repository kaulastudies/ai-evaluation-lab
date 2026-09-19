class EventProcessor:
    """Mutation: treats changed payload as a new event."""

    def __init__(self):
        self.total = 0
        self.processed = set()

    def handle(self, event_id, amount):
        key = (event_id, amount)
        if key in self.processed:
            return False

        self.processed.add(key)
        self.total += amount
        return True
