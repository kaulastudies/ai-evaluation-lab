class EventProcessor:
    """Synthetic at-least-once event processor with a duplicate-delivery bug."""

    def __init__(self):
        self.total = 0

    def handle(self, event_id, amount):
        self.total += amount
        return True
