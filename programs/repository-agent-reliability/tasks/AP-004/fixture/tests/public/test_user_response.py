import unittest

from app.user_response import UserResponseBuilder


class PublicUserResponseTests(unittest.TestCase):
    def test_happy_path_response(self):
        builder = UserResponseBuilder()
        status, body = builder.build(
            {
                "id": 7,
                "name": "Ada",
                "email": "ada@example.test",
                "nickname": "ada",
                "password_hash": "internal-only",
            }
        )

        self.assertEqual(status, 200)
        self.assertEqual(body["id"], 7)
        self.assertEqual(body["name"], "Ada")
        self.assertEqual(body["email"], "ada@example.test")
        self.assertEqual(body["nickname"], "ada")


if __name__ == "__main__":
    unittest.main()
