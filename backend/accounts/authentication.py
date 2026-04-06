from datetime import timedelta
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


TOKEN_EXPIRED_SECONDS = 24 * 60 * 60  # 24 小時


class ExpiringTokenAuthentication(TokenAuthentication):
    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)
        now = timezone.now()
        if (now - token.created).total_seconds() > TOKEN_EXPIRED_SECONDS:
            # Token 過期，刪除並報錯
            token.delete()
            raise AuthenticationFailed('Token 已過期，請重新登入。')
        return user, token
