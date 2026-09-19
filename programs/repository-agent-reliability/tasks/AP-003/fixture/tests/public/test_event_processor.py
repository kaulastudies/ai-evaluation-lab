import unittest

from app.event_processor import EventProcessor


class PublicEventProcessorTests(unittest.TestCase):
    def test_first_event_applies(self):
        processor = EventProcessor()
        accepted = processor.handle("evt-1", 10)
        self.assertTrue(accepted)
        self.assertEqual(processor.total, 10)

    def test_distinct_events_apply(self):
        processor = EventProcessor()
        first = processor.handle("evt-1", 10)
        second = processor.handle("evt-2", 7)
        self.assertTrue(first)
        self.assertTrue(second)
        self.assertEqual(processor.total, 17)


if __name__ == "__main__":
    unittest.main()
