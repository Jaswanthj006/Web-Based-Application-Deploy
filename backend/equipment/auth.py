"""Custom token authentication using equipment.AuthToken (no djangorestframework-authtoken)."""
from rest_framework import authentication
from .models import AuthToken


class TokenAuthentication(authentication.BaseAuthentication):
    keyword = 'Token'

    def authenticate(self, request):
        auth = request.META.get('HTTP_AUTHORIZATION') or ''
        if auth.startswith(self.keyword + ' '):
            key = auth[len(self.keyword) + 1:].strip()
        elif request.GET.get('token'):
            key = request.GET.get('token').strip()
        else:
            return None
        if not key:
            return None
        try:
            token = AuthToken.objects.select_related('user').get(key=key)
            return (token.user, token)
        except AuthToken.DoesNotExist:
            return None
