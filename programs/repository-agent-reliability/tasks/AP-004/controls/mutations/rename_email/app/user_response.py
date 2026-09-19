class UserResponseBuilder:
    """Mutation: renames a required public response field."""

    def build(self, user):
        return 200, {
            "id": user["id"],
            "name": user["name"],
            "email_address": user["email"],
            "nickname": user.get("nickname"),
        }
