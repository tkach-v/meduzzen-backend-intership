import logging
from urllib.parse import parse_qs

from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from jwt import decode as jwt_decode
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken


@database_sync_to_async
def get_user(validated_token):
    try:
        return get_user_model().objects.get(id=validated_token["user_id"])

    except get_user_model().DoesNotExist:
        return AnonymousUser()


class JwtAuthMiddleware(BaseMiddleware):
    """ JWT Token authorization for channels"""
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        close_old_connections()
        token = parse_qs(scope["query_string"].decode("utf8"))["token"][0]
        try:
            UntypedToken(token)
        except (InvalidToken, TokenError) as e:
            logger = logging.getLogger(__name__)
            logger.error(e)
            return None
        else:
            decoded_data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            scope["user"] = await get_user(validated_token=decoded_data)

        return await super().__call__(scope, receive, send)


def jwt_auth_middleware_stack(inner):
    return JwtAuthMiddleware(AuthMiddlewareStack(inner))
