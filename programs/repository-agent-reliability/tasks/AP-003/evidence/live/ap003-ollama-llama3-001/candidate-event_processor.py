class EventProcessor:
    """Synthetic at-least-once event processor with idempotent event handling."""

    def __init__(self):
        self.total = 0
        self.event_id = None

    def handle(self, event_id, amount):
        if event_id == self.event_id:
            return True
        self.event_id = event_id
        self.total += amount
        return True
