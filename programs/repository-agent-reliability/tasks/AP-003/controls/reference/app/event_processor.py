class EventProcessor:
    """Synthetic idempotent event processor."""

    def __init__(self):
        self.total = 0
        self.processed_event_ids = set()

    def handle(self, event_id, amount):
        if event_id in self.processed_event_ids:
            return False

        self.processed_event_ids.add(event_id)
        self.total += amount
        return True
