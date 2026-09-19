class UserResponseBuilder:
    """Mutation: leaks an internal storage field into the public response."""

    def build(self, user):
        return 200, {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "nickname": user.get("nickname"),
            "password_hash": user.get("password_hash"),
        }
