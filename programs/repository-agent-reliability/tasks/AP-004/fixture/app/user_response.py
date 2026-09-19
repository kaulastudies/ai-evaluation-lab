class UserResponseBuilder:
    """Build a public response from an internal user record."""

    def build(self, user):
        body = {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
        }

        if "nickname" in user:
            body["nickname"] = user["nickname"]

        # BUG: internal storage detail is exposed to API clients.
        body["password_hash"] = user.get("password_hash")
        return 200, body
