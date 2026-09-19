class EventProcessor:
    """Synthetic at-least-once event processor with a duplicate-delivery bug."""

    def __init__(self):
        self.total = 0

    def handle(self, event_id, amount):
        # BUG: retrying the same event applies the side effect again.
        self.total += amount
        return True
