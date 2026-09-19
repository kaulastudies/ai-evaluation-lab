class EventProcessor:
    """Mutation: deduplicates by amount instead of event identity."""

    def __init__(self):
        self.total = 0
        self.processed_amounts = set()

    def handle(self, event_id, amount):
        if amount in self.processed_amounts:
            return False

        self.processed_amounts.add(amount)
        self.total += amount
        return True
