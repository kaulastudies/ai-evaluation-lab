class UserResponseBuilder:
    """Mutation: changes the public id type from integer to string."""

    def build(self, user):
        return 200, {
            "id": str(user["id"]),
            "name": user["name"],
            "email": user["email"],
            "nickname": user.get("nickname"),
        }
