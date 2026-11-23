import unittest

from app.record_transformer import RecordTransformer


class PublicRecordTransformerTests(unittest.TestCase):
    def test_happy_path_records(self):
        rows = [
            {
                "id": "a-1",
                "value": 5,
                "active": True,
                "note": "ready",
            },
            {
                "id": "b-2",
                "value": 12,
                "active": True,
                "note": "queued",
            },
        ]

        result = RecordTransformer().transform(rows)

        self.assertEqual(
            result,
            [
                {
                    "id": "a-1",
                    "value": 5,
                    "active": True,
                    "note": "ready",
                },
                {
                    "id": "b-2",
                    "value": 12,
                    "active": True,
                    "note": "queued",
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()
