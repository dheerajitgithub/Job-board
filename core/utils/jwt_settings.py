"""JWT response in login is handled here"""

import logging
import datetime
import pytz
from rest_framework.serializers import ValidationError
# from accounts.authentication.v1.utils.user_permissions import get_user_permissions
from accounts.models import (AccountsBlacklistTokensModel,  AccountsLoginAnalyticsModel, AccountsUserResumeModel)
from core.settings import logger

api_logger = logging.LoggerAdapter(logger, {"app_name": "JWTSettings"})

def jwt_response_payload_handler(token, user=None, request=None, issued_at=None):
    """
    Custom response payload handler.
    """
    response = {}
    try:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        api_logger.info(ip)
        if request.data.get("re_login"):
            api_logger.info("Checking for existing blacklist token...")
            try:
                token_obj = AccountsBlacklistTokensModel.objects.get(
                    user=user, is_login=True
                )
                token_obj.is_login = False
                token_obj.is_delete = True
                token_obj.save()
                AccountsBlacklistTokensModel.objects.create(
                    user=user, token=token, is_login=True
                )
                api_logger.info("Existing token found and updated.")
            except Exception:
                AccountsBlacklistTokensModel.objects.create(
                    user=user, token=token, is_login=True
                )
                api_logger.info("Generated new token.")
        else:
            try:
                AccountsBlacklistTokensModel.objects.get(user=user, is_login=True)
                raise ValidationError({"message": "user have active session"})
            except AccountsBlacklistTokensModel.DoesNotExist:
                AccountsBlacklistTokensModel.objects.create(
                    user=user, token=token, is_login=True
                )
        api_logger.info(f"User Agent: {request.user_agent}")
        api_logger.info(f"Issued At: {issued_at}")
        default_login_analytics = {
            "user" : user, "ip_address" : ip, "device_name" : request.user_agent
        }
        login_analytics_obj, created = AccountsLoginAnalyticsModel.objects.get_or_create(
            user=user, ip_address=ip, device_name=request.user_agent,
            defaults=default_login_analytics
        )

        api_logger.info(f"Login Analytics Created : {created}")

        login_analytics_obj.login_count += 1
        login_analytics_obj.save()
        first_login = False
        if not user.last_login:
            first_login = True
            user.last_login = datetime.datetime.now(pytz.utc)

            user.save()
        # permissions = get_user_permissions(user)
        
        is_cv_uploaded = False
        if user.user_type == "CANDIDATE":
            is_cv_uploaded = AccountsUserResumeModel.objects.filter(candidate=user).exists()
        response.update(
            {
                "token": token,
                "username": user.first_name + " " + user.last_name,
                "email": user.email,
                "user_id": str(user.id),
                "profile_picture": user.profile_picture,
                "is_super_user" : user.is_superuser,
                "user_type" : user.user_type,
                # "first_login": first_login,
                "ip_address": ip,
                "requeststatus": 1,
                "is_verified": user.is_verified,
                # "role" : permissions
                # "timezone_info": timezone_info,
                "is_cv_uploaded": is_cv_uploaded,
            }
        )

        if user.user_type in ["EMPLOYER","ADMIN"]:
            response.update({
                "company_id":str(user.company.id),
                "company_name":user.company.title
            })
        
        return response
    except Exception as e:
        print("custom JWT error : ", e)
        if str(e)=="{'message': ErrorDetail(string='user have active session', code='invalid')}":
            raise ValidationError({"message": "user have active session"}) from e
        raise ValidationError({"message": "Something went wrong", "data": str(e)}) from e
