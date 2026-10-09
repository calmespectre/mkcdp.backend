from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser


@database_sync_to_async
def _resolve_user(token):
    from accounts.models import User
    from rest_framework_simplejwt.tokens import AccessToken
    try:
        access = AccessToken(token)
        user_id = access.get("user_id")
        return User.objects.get(id=user_id)
    except Exception:
        return AnonymousUser()


class JWTAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get("query_string", b"").decode())
        tokens = query.get("token", [])
        token = tokens[0] if tokens else None
        if token:
            scope["user"] = await _resolve_user(token)
        else:
            scope["user"] = AnonymousUser()
        return await self.inner(scope, receive, send)