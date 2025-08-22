"""Authentication utils"""

import logging
import jwt
from rest_framework_jwt.authentication import (
    JSONWebTokenAuthentication,
    get_authorization_header,
)
from rest_framework_jwt.settings import api_settings
from rest_framework import exceptions
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from functools import wraps
from django.utils.encoding import smart_str
from django.utils.translation import gettext as _
from core.settings import SECRET_KEY, logger
from core.utils.contants import SIGNATURE_EXPIRED_MSG
from accounts.models import AccountsBlacklistTokensModel

logger = logging.LoggerAdapter(
    logger, {"app_name": "core.utils.authentications"})

class CustomAuthentication(JSONWebTokenAuthentication):
    """
    Authentication Class for users
    """

    www_authenticate_realm = "api"

    def get_token_from_request(self, request):
        """
            Extracts the token from the given HTTP request.
        """
        auth = get_authorization_header(request).split()
        auth_header_prefix = api_settings.JWT_AUTH_HEADER_PREFIX.lower()
        try:
            backlist_obj = AccountsBlacklistTokensModel.objects.get(
                token=auth[1].decode("utf-8"), is_login=True)
        except Exception as e:
            msg = _("Signature has expired.")
            logger.warning(e)
            raise exceptions.AuthenticationFailed(msg)

        if not auth:
            if api_settings.JWT_AUTH_COOKIE:
                return request.COOKIES.get(api_settings.JWT_AUTH_COOKIE)
            return None

        if smart_str(auth[0].lower()) != auth_header_prefix:
            return None

        if len(auth) == 1:
            msg = _("Invalid Authorization header. No credentials provided.")
            logger.warning(msg)
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _(
                "Invalid Authorization header. Credentials string "
                "should not contain spaces."
            )
            raise exceptions.AuthenticationFailed(msg)

        if not backlist_obj.is_login:
            msg = _(SIGNATURE_EXPIRED_MSG)
            logger.warning(msg)
            raise exceptions.AuthenticationFailed(msg)

        return auth[1]


# class CustomSupportAuthentication(JSONWebTokenAuthentication):
#     """
#     Authentication Class for users
#     """

#     www_authenticate_realm = "api"

#     def get_token_from_request(self, request):
#         print("we in")
#         """
#             Extracts the token from the given HTTP request.
#         """
#         auth = get_authorization_header(request).split()
#         auth_header_prefix = api_settings.JWT_AUTH_HEADER_PREFIX.lower()
#         print(auth[1])
#         try:
#             backlist_obj = AccountsSupportBlacklistTokensModel.objects.get(
#                 token=auth[1].decode("utf-8"), is_login=True)
#         except Exception as e:
#             msg = _("Signature has expired.")
#             logger.warning(e)
#             raise exceptions.AuthenticationFailed(msg)
#         print(98)
#         if not auth:
#             if api_settings.JWT_AUTH_COOKIE:
#                 return request.COOKIES.get(api_settings.JWT_AUTH_COOKIE)
#             return None
#         print(99)
#         if smart_str(auth[0].lower()) != auth_header_prefix:
#             return None
#         print(100)
#         if len(auth) == 1:
#             msg = _("Invalid Authorization header. No credentials provided.")
#             logger.warning(msg)
#             raise exceptions.AuthenticationFailed(msg)
#         elif len(auth) > 2:
#             msg = _(
#                 "Invalid Authorization header. Credentials string "
#                 "should not contain spaces."
#             )
#             raise exceptions.AuthenticationFailed(msg)
#         print(101)

#         if not backlist_obj.is_login:
#             msg = _(SIGNATURE_EXPIRED_MSG)
#             logger.warning(msg)
#             raise exceptions.AuthenticationFailed(msg)
#         print(102)
#         return auth[1]

#     def get_user_from_payload(self, payload):
#         print(9999)
#         user_id = payload.get("user_id")
#         try:
#             return SupportUserModel.objects.get(id=user_id)
#         except SupportUserModel.DoesNotExist:
#             raise exceptions.AuthenticationFailed("User not found.")
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError



class CustomAuthenticationWithoutLogout(JSONWebTokenAuthentication):
    """
    Authentication Class for users
    """

    www_authenticate_realm = "api"

    def get_token_from_request(self, request):
        """
            Extracts the token from the given HTTP request.
        """
        auth = get_authorization_header(request).split()
        # auth_header_prefix = api_settings.JWT_AUTH_HEADER_PREFIX.lower()
        # try:
        #     backlist_obj = AccountsBlacklistTokensModel.objects.get(
        #         token=auth[1].decode("utf-8"), is_login=True)
        # except Exception as e:
        #     msg = _("Signature has expired.")
        #     logger.warning(e)
        #     raise exceptions.AuthenticationFailed(msg)

        # if not auth:
        #     if api_settings.JWT_AUTH_COOKIE:
        #         return request.COOKIES.get(api_settings.JWT_AUTH_COOKIE)
        #     return None

        # if smart_str(auth[0].lower()) != auth_header_prefix:
        #     return None

        # if len(auth) == 1:
        #     msg = _("Invalid Authorization header. No credentials provided.")
        #     logger.warning(msg)
        #     raise exceptions.AuthenticationFailed(msg)
        # elif len(auth) > 2:
        #     msg = _(
        #         "Invalid Authorization header. Credentials string "
        #         "should not contain spaces."
        #     )
        #     raise exceptions.AuthenticationFailed(msg)

        # if not backlist_obj.is_login:
        #     msg = _(SIGNATURE_EXPIRED_MSG)
        #     logger.warning(msg)
        #     raise exceptions.AuthenticationFailed(msg)

        return auth[1]



# def require_support_api_key(view_func):
#     @wraps(view_func)
#     def _wrapped_view(request, *args, **kwargs):
#         api_key = request.headers.get('X-API-KEY')
#         if api_key != SUPPORT_API_KEY:
#             return JsonResponse({'error': 'Invalid API key'}, status=403)
#         return view_func(request, *args, **kwargs)
#     return _wrapped_view


