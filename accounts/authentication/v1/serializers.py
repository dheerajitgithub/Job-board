"""Serializer for accounts.authentication"""
import datetime
import logging
from django.forms import ValidationError
import random,pytz
import threading
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext as _
from django.db.models import Q
from django.template.loader import render_to_string
from django.db import transaction
from core.settings import logger as job_board_logger
from core.settings import UI_HOST
from core.utils.contants import (
    COMPANY_VALIDATION_MESSAGE,
    COMPANY_WEBSITE_ALREADY_EXISTS,
    EMAIL_ALREADY_EXISTS,
    PASSWORD_STRING_VALIDATION,
    PHONE_NUMBER_ALREADY_EXISTS,
    USER_NOT_ACTIVE,
    INCORRECT_EMAIL,
    INCORRECT_PASSWORD,
    USER_DOESNT_EXIST_MSG,
    NEW_PASSWORD_SAME_AS_OLD_PASSWORD,
    PASSWORD_STRING_VALIDATION_MSG,
    INCORRECT_CURRENT_PASSWORD,
    CONFIRM_PASSWORD_VALIDATION,
    USER_NOT_VERIFIED
)
from core.utils.emails import send_an_email
from core.utils.utils import check_password_custom, crypt_password, generate_alphanumeric_code, is_filter_required
from accounts.authentication.v1.utils.password_manager import (
    decode_jwt,
    forgot_password_send_email,
)
from accounts.models import (
    AccountsBlacklistTokensModel,
    AccountsUserModel,
)
from employer.models import CompanyDetailModel, EmployerJobDetailsModel

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
jwt_get_username_from_payload = api_settings.JWT_PAYLOAD_GET_USERNAME_HANDLER

api_logger = logging.LoggerAdapter(job_board_logger,{"app_name":"accounts.authentication.v1.serializers"})

class CustomJWTSerializer(JSONWebTokenSerializer):
    """Custom JWT serializer"""
    username_field = "email"
    api_logger = logging.LoggerAdapter(job_board_logger, {"app_name": "CustomJWTSerializer"})

    def validate(self, data):
        """validating user input for login"""
        try:
            password = data.get("password")
            email = data.get("email")
            error_list = []
            user_obj = get_user_model().objects.get(Q(email__iexact=email) | Q(username__iexact=email))
            self.api_logger.info(f"User Id: {user_obj.id}")
            
            if not user_obj.check_password(password):
                error_list.append({
                    "password": INCORRECT_PASSWORD
                    })
                raise serializers.ValidationError({"message": error_list})

            if not user_obj.is_active:
                error_list.append({"email": USER_NOT_ACTIVE})

                raise serializers.ValidationError({"message": error_list})
            
            if not user_obj.is_verified:
                error_list.append({"unregistered": USER_NOT_VERIFIED})

                raise serializers.ValidationError({"message":error_list})
            

            credentials = {"username": user_obj.email, "password": password}
            user = authenticate(**credentials)
            if user:
                self.api_logger.info(f"Authenticated user: {user_obj.id}")
                payload = jwt_payload_handler(user)
                return {"token": jwt_encode_handler(payload), "user": user}
            else:
                error_list.append({"authentication": "Failed"})
                raise serializers.ValidationError({"message": "Authentication failed"})

        except get_user_model().DoesNotExist:
            # error_list.append({"email": "User with this email does not exist"})
            raise serializers.ValidationError(
                {"message": {"email": "Uh-oh! It appears that the credentials entered is incorrect."}}
            )
        except Exception as e:
            if (
                str(e)
                == "{'message': [{'password': ErrorDetail(string='Uh-oh! It appears that the password entered is incorrect.', code='invalid')}]}"
            ):
                raise serializers.ValidationError(
                    {"message": {"password": INCORRECT_PASSWORD}}
                )
            elif (
                str(e)
                == "{'message': [{'email': ErrorDetail(string='Uh-oh! It appears that the account is not yet active', code='invalid')}]}"
            ):
                raise serializers.ValidationError(
                    {"message": {"email": USER_NOT_ACTIVE}}
                )
            elif (
                str(e)
                == "{'message': [{'unregistered': ErrorDetail(string='Uh-oh! It appears that the account is not yet verified', code='invalid')}]}"
            ):
                raise serializers.ValidationError(
                    {"message": {"unregistered": USER_NOT_VERIFIED}}
                )
            raise serializers.ValidationError(str(e))

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        return (instance, validated_data)


class AccountsAuthForgotPasswordSerializer(serializers.Serializer):
    """AccountsAuthForgotPasswordSerializer"""
    email = serializers.CharField(required=True)   
    logger = logging.LoggerAdapter(
        job_board_logger, {"app_name": "AccountsAuthForgotPasswordSerializer"}
    )

    def validate(self, attrs):
        """Validate forgot password"""
        if not get_user_model().objects.filter(email=attrs["email"]):
            raise serializers.ValidationError(INCORRECT_EMAIL)
        return attrs

    def create(self, validated_data):
        """Creation forgot password"""
        email = validated_data["email"]
        ui_host = UI_HOST
        forgot_password_send_email(email, ui_host)
        return validated_data

    def update(self, instance, validated_data):
        return (instance, validated_data)

class AccountsAuthForgotPasswordUpdateSerializer(serializers.Serializer):
    """AccountsAuthForgotPasswordUpdateSerializer"""

    user_id = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    logger = logging.LoggerAdapter(
        job_board_logger, {"app_name": "AccountsAuthForgotPasswordUpdateSerializer"}
    )

    def validate(self, attrs):
        """Validate forgot password"""
        decoded_jwt = decode_jwt(attrs["user_id"])
        if isinstance(decoded_jwt, str):
            raise serializers.ValidationError(decoded_jwt)
        try:
            user_instance = get_user_model().objects.get(id=decoded_jwt["user_id"])
        except get_user_model().DoesNotExist:
            raise serializers.ValidationError(USER_DOESNT_EXIST_MSG)

        if user_instance.check_password(attrs["new_password"]):
            raise serializers.ValidationError(NEW_PASSWORD_SAME_AS_OLD_PASSWORD)

        if not check_password_custom(attrs["new_password"]):
            raise serializers.ValidationError(PASSWORD_STRING_VALIDATION_MSG)
        attrs["user_id"] = decoded_jwt["user_id"]
        return attrs

    def create(self, validated_data):
        """Creation forgot password"""
        user_instance = get_user_model().objects.get(id=validated_data["user_id"])
        user_instance.set_password(validated_data["new_password"])
        user_instance.save()
        return validated_data

    def update(self, instance, validated_data):
        return (instance, validated_data)




class AccountsAuthLogoutSerializer(serializers.Serializer):
    """AccountsAuthLogoutSerializer"""

    logger = logging.LoggerAdapter(
        job_board_logger, {"app_name": "AccountsAuthLogoutSerializer"}
    )

    def validate(self, attrs):
        """validate logout"""
        return attrs

    def create(self, validated_data):
        """creation logout"""
        request = self.context["request"]
        with transaction.atomic():
            login_obj = AccountsBlacklistTokensModel.objects.get(user=request.user, is_login=True)
            login_obj.is_login = False
            login_obj.is_delete = True
            login_obj.save()
        return validated_data

    def update(self, instance, validated_data):
        """update logout"""
        return (instance, validated_data)


class AccountsAuthChangePasswordSerializer(serializers.Serializer):
    """AccountsAuthChangePasswordSerializer"""

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    logger = logging.LoggerAdapter(
        job_board_logger, {"app_name": "AccountsAuthChangePasswordSerializer"}
    )

    def validate(self,attrs):
        """validate new password"""
        request = self.context["request"]
        user_instance = request.user
        if not user_instance.check_password(attrs["old_password"]):
            raise serializers.ValidationError(INCORRECT_CURRENT_PASSWORD)

        if attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError(NEW_PASSWORD_SAME_AS_OLD_PASSWORD)

        if not check_password_custom(attrs["new_password"]):
            raise serializers.ValidationError(PASSWORD_STRING_VALIDATION)
        
        if not attrs["new_password"] == attrs["confirm_password"]:
            raise serializers.ValidationError(CONFIRM_PASSWORD_VALIDATION)
        return attrs

    def create(self, validated_data):
        """Creation change password"""
        request = self.context["request"]
        user_instance = request.user
        user_instance.set_password(validated_data["new_password"])
        user_instance.save()
        return validated_data

    def update(self, instance, validated_data):
        return (instance, validated_data)


class AccountsUserProfileSerializer(serializers.ModelSerializer):
    role_id = serializers.CharField(source = "role.id", allow_null=True,read_only=True)
    role_name = serializers.CharField(source = "role.role_name", allow_null=True,read_only=True)

    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "username",
            "email",
            "user_type",
            "profile_picture",
            "country_code",
            "last_login",
            "role_name",
            "ctc_per_hour",
            "role_id",
            "is_active"
        ]

class AccountsUserPartialSerializer(serializers.ModelSerializer):

    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "username",
            "email",
            "profile_picture"
        ]



# class AccountsAuthenticationUserProfileUpdateSerializer(serializers.ModelSerializer):
#     company_title = serializers.CharField(
#         # source="company.title",
#         required=False,
#     )
#     id = serializers.UUIDField()
#     class Meta:
#         model = AccountsUserModel
#         fields = [
#             "id",
#             "first_name",
#             "last_name",
#             "company_title",
#             "phone_number",
#             "country_code",
#             "profile_picture"
#         ]

#     def validate(self, data):
#         if not self.Meta.model.objects.filter(pk=data['id']).exists():
#             raise serializers.ValidationError('Incorrect User ID')
#         return data
#     def create(self, validated_data):
#         with transaction.atomic():
#             queryset = self.Meta.model.objects.all()
#             queryset.filter(pk=validated_data['id']).update(
#                 **{
#                     # 'first_name' :  validated_data['first_name'],
#                     'last_name' : validated_data['last_name'],
#                     'phone_number' : validated_data['phone_number'],
#                     # "country_code":validated_data["county_code"],
#                     "profile_picture":validated_data["profile_picture"]
#              }
#             )
#             company_instance = queryset.company
#             print("coomppany",company_instance)
#             if company_instance:
#                 company_instance.title = validated_data['company_title']
#                 company_instance.save()
#         return validated_data

class AccountsAuthenticationUserProfileUpdateSerializer(serializers.ModelSerializer):
    company = serializers.CharField(
        required=False,
    )
    company_website = serializers.CharField(
        required=False
    )
    company_profile_picture = serializers.CharField(
        required=False
    )
    id = serializers.UUIDField()

    class Meta:
        model = AccountsUserModel
        fields = [
            "id",
            "first_name",
            "last_name",
            "company",
            "company_website",
            "phone_number",
            "country_code",
            "profile_picture",
            "company_profile_picture"
        ]

    def validate(self, data):
        company = data.get("company")
        company_website = data.get("company_website")

        if not self.Meta.model.objects.filter(pk=data['id']).exists():
            raise serializers.ValidationError('Incorrect User ID')
        
        if is_filter_required("company_website", data):
            if CompanyDetailModel.objects.filter(company_website = company_website).exists():
                raise serializers.ValidationError("Company  with this website already exist's")
        return data

    def create(self, validated_data):
        with transaction.atomic():
            user = self.Meta.model.objects.select_related('company').get(pk=validated_data['id'])
            
            # Update user fields
            update_fields = {}
            for field in ['first_name', 'last_name', 'phone_number', 'country_code', 'profile_picture']:
                if field in validated_data:
                    update_fields[field] = validated_data[field]
            
            self.Meta.model.objects.filter(pk=user.pk).update(**update_fields)
            
            user.refresh_from_db()
            
            if 'company' in validated_data and user.company:
                user.company.title = validated_data['company']
                user.company.save()
            if 'company_website' in validated_data and user.company:
                user.company.company_website = validated_data['company_website']
                user.company.save()
            if 'profile_picture' in validated_data and user.company:
                user.company.profile_picture = validated_data['profile_picture']
                user.company.save()
        return validated_data

class AccountsAuthenticationGetUserProfileInfoSerializer(serializers.ModelSerializer):
    company_title = serializers.CharField(
        source="company.title",
        allow_blank=True,
        default=None,
        required = False
    )
    company_website = serializers.CharField(
        source="company.company_website",
        allow_blank=True,
        default=None,
        required = False
    )
    company_email = serializers.CharField(
        source = "company.company_email",
        allow_blank = True,
        default = None,
        required = False
    )
    company_logo = serializers.CharField(
        source = "company.company_logo",
        allow_blank = True,
        default = None,
        required = False
    )
    company_phone_number = serializers.CharField(
        source = "company.phone_number",
        allow_blank = True,
        default = None,
        required = False
    )
    class Meta:
        model = AccountsUserModel
        fields = [
            "id",
            "user_id",
            "username",
            "email",
            "profile_picture",
            "country_code",
            "phone_number",
            "first_name",
            "last_name",
            "short_name",
            "company",
            "company_title",
            "company_website",
            "company_email",
            "company_logo",
            "company_phone_number",
            "last_login",
            "linkedin_url",
            "user_type",
            "designation",
            "user_skills",
            "is_staff",
            "is_active",
            "is_verified",
            "is_superuser",
            "is_admin"
        ]

    # data = serializers.JSONField(required=False)

    # def create(self, validated_data):
    #     user = self.context["request"].user
    #     data = AccountsAuthenticationUserProfileUpdateSerializer(user, many=False).data
    #     validated_data["data"] = data
    #     return validated_data
    

class AccountsAuthenticationUsersRegistrationCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True)
    company = serializers.CharField(required=True)
    company_website = serializers.CharField(required=True) 
    country_code = serializers.CharField(required=True)



    logger = logging.LoggerAdapter(
        job_board_logger, {"app_name": "AccountsAuthenticationUsersRegistrationCreateSerializer"}
    )
    
    class Meta:
        model = AccountsUserModel
        fields = "__all__"

    def validate(self, data):
        user_queryset = AccountsUserModel.objects.all()
        error_list = []

        company_queryset = CompanyDetailModel.objects.all()
        country_code = str(data["country_code"]).strip()
        phone_number = str(data["phone_number"]).strip()

        if user_queryset.filter(email = data["email"],is_verified = True).exists():
            error_list.append({"email": "Email already exist's"})

        if user_queryset.filter(email = data["email"], is_verified=False).exists():
            error_list.append({"email": "user is not yet verified"})

        if company_queryset.filter(company_website=data["company_website"]).exists():
            error_list.append({"company_website": "Company with this website already exist's "})
        
        if user_queryset.filter(phone_number=data["phone_number"],country_code=data["country_code"]).exists():
                error_list.append({"phone_number": "Phone number already exists for this country code"})
        
        if company_queryset.filter(title=data["company"]).exists():
            error_list.append({"company": "Company with this name already exist's"})
        
        if len(error_list) > 0:
            raise serializers.ValidationError(
                {"message": error_list}
                )
        
        return data

    def create(self, validated_data):
        initial_data = validated_data.copy()
        company_name = validated_data.pop("company")
        password = validated_data.pop("password")
        company_website = validated_data.pop("company_website")
        company_instance = CompanyDetailModel.objects.create(
                title=company_name,
                temp_referral_code=generate_alphanumeric_code(8),
                # user_type = "EMPLOYER",
                company_website=company_website,
                is_active=True
            )


        generated_otp = random.randint(100000, 999999)
        otp_expiry_time = datetime.datetime.now(pytz.utc) + datetime.timedelta(minutes=3)
        user_instance = AccountsUserModel.objects.create(
            company=company_instance,
            is_admin=True,
            otp=generated_otp,
            otp_expired_time=otp_expiry_time,
            **validated_data
        )
        user_instance.set_password(password)
        user_instance.user_type = "EMPLOYER"
        user_instance.username = user_instance.first_name + " " + user_instance.last_name
        user_instance.save()
        
        context = {
            "otp": str(generated_otp),
            "username" : user_instance.username,
            "otp_expiry_minutes": "3:00",
        }
        
        message = render_to_string("auth/send_otp.html", context)

        thread = threading.Thread(
            target=send_an_email,
            kwargs={
                "receiver_email": [validated_data["email"]],
                "subject": "JobBoard | Validate your account with OTP and complete your sign up!",
                "body": message,
            },
        )

        thread.start()

        initial_data["is_verified"] = user_instance.is_verified
        
        return initial_data
    
from django.utils import timezone

class AccountsAuthenticationVerifyOtpSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    # is_activating = serializers.BooleanField(required=True)

    logger = logging.LoggerAdapter(
        job_board_logger, {"app_name": "AccountsAuuthenticationVerifyOtpSerializer"}
    )

    class Meta:
        model = AccountsUserModel
        fields = ["email", "otp"]

    def validate(self, data):
        queryset = AccountsUserModel.objects.all()
        
        if not queryset.filter(email=data["email"].lower()).exists():
            raise serializers.ValidationError(
                {
                    "message": [
                        {"email": "User with this email does not exists"}
                    ]
                }
            )
        if not queryset.filter(
            email=data["email"].lower(), otp=int(data["otp"])
        ).exists():
            raise serializers.ValidationError(
                {
                    "message": [
                        {"otp": "Oops! The verification code you entered is incorrect"}
                    ]
                }
            )
        current_time_utc = timezone.now()
        if queryset.get(email=data["email"].lower(), otp=int(data["otp"])).otp_expired_time < current_time_utc:
            self.logger.info("OTP Expired")
            raise serializers.ValidationError(
                {
                    "message": 
                        [{"otp": "Oops! The verification code you entered is expired"}]
                }
            )
        return data

    def create(self, validated_data):
        data = validated_data
        user_instance = AccountsUserModel.objects.get(
            email=data["email"].lower(), otp=int(data["otp"])
        )
        self.logger.info(
            "OTP TIme: {} - Current time : {}".format(
                user_instance.otp_expired_time.replace(tzinfo=None),
                datetime.datetime.now(pytz.utc),
            )
        )
        user_instance.email = validated_data["email"].lower()
        user_instance.is_verified = True
        user_instance.is_active = True
        user_instance.save()
        
        
        context = {
            "FRONTEND_URL" : f"{UI_HOST}/auth/login/",
            "username" : user_instance.username
        }
        message = render_to_string("auth/signUpAfterOtpVerification.html", context)
        thread=threading.Thread(
            target=send_an_email,
            kwargs={
                "receiver_email":[user_instance.email],
                "subject": "JobBoard | Your email is verified!",
                "body":message
            }
        )
        thread.start()

        return validated_data
    
class AccountsAuthenticationResendOtpSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    # forgot_password = serializers.BooleanField(default=False)

    logger = logging.LoggerAdapter(
        job_board_logger, {"app_name": "AccountsAuthenticationResendOtpSerializer"}
    )

    class Meta:
        model = AccountsUserModel
        fields = ["email"]

    def validate(self, data):
        queryset = get_user_model().objects.all()
        if not queryset.filter(email=data["email"].lower()).exists():
            raise serializers.ValidationError({"message": "User does not exist"})

        return data

    def create(self, validated_data):
        data = validated_data
        user_obj = AccountsUserModel.objects.get(email=data["email"].lower())
        generated_otp = random.randint(100000, 999999)
        otp_expiry_time = datetime.datetime.now(pytz.utc) + datetime.timedelta(minutes=3)
        user_obj.otp = generated_otp
        user_obj.otp_expired_time = otp_expiry_time
        user_obj.save()
        context = {
            "otp": str(generated_otp),
            "username" : user_obj.username
        }
        message = render_to_string("auth/resend_otp.html", context)
        subject="JobBoard | Validate your account with OTP and complete your sign up!"
        thread = threading.Thread(
             target=send_an_email,
             kwargs={
                 "receiver_email": [data["email"]],
                 "subject": "JObBoard - Verify your OTP",
                 "body": message,
             },
        )
        thread.start()
        self.logger.info("OTP Sent")
        return validated_data