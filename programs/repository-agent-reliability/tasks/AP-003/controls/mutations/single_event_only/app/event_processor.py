class EventProcessor:
    """Mutation: only the first event in the processor lifetime is accepted."""

    def __init__(self):
        self.total = 0
        self.processed_any = False

    def handle(self, event_id, amount):
        if self.processed_any:
            return False

        self.processed_any = True
        self.total += amount
        return True
