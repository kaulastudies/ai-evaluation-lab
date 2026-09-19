class UserResponseBuilder:
    """Build the stable public user-response contract."""

    def build(self, user):
        return 200, {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "nickname": user.get("nickname"),
        }
