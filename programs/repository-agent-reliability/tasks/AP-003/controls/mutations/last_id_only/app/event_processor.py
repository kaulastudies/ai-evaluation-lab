class EventProcessor:
    def __init__(self):
        self.total = 0
        self.last = None
    def handle(self, event_id, amount):
        if event_id == self.last:
            return False
        self.last = event_id
        self.total += amount
        return True
