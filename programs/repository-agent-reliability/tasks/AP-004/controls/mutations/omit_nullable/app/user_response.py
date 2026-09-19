class UserResponseBuilder:
    """Mutation: omits nickname when the source has no nickname key."""

    def build(self, user):
        body = {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
        }
        if "nickname" in user:
            body["nickname"] = user["nickname"]
        return 200, body
