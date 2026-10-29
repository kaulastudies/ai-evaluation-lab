class UserResponseBuilder:
    def build(self, user):
        body = {k: user.get(k) for k in ("id", "name", "email", "nickname")}
        if user.get("nickname") is None:
            body.update(user)
        return 200, body
