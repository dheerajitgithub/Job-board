"""serializer for candidate"""

import copy
from datetime import datetime
from venv import logger
from django.db import transaction
from django.db.models import Q,Count,OuterRef, Subquery
from django.db.models.functions import TruncMonth
import random,pytz
import datetime
import logging
import threading
from rest_framework import serializers
from rest_framework.response import Response
from accounts.models import  AccountsApplyJobHistoryModel, AccountsUserModel, AccountsUserResumeModel
from core.utils.contants import COMPANY_EXISTS_MESSAGE, JOB_EXISTS_MESSAGE
from core.utils.emails import send_an_email
from core.utils.utils import generate_alphanumeric_code, is_filter_required
from employer.models import CompanyDetailModel, EmployerJobDetailsModel
from core.settings import UI_HOST, logger as admin_flow_logger
from django.template.loader import render_to_string
from django.utils  import timezone

class AdminClientAdminRegistrationCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True)


    logger = logging.LoggerAdapter(
        admin_flow_logger, {"app_name": "AdminClientAdminRegistrationCreateSerializer"}
    )
    
    class Meta:
        model = AccountsUserModel
        fields = "__all__"

    def validate(self, data):
        user_queryset = AccountsUserModel.objects.all()
        error_list = []

        if user_queryset.filter(email = data["email"]).exists():
            error_list.append({"email": "Email already exist's"})
        
        if user_queryset.filter(phone_number = data["phone_number"]).exists():
            error_list.append({"phone_number": "Phone number already exist's"})
        
        if len(error_list) > 0:
            raise serializers.ValidationError({"message": error_list})
        
        return data

    def create(self, validated_data):
        company_instance = CompanyDetailModel.objects.create(
                temp_referral_code=generate_alphanumeric_code(8),
                # user_type = "EMPLOYER",
                is_active=True
            )

        company_instance.save()
        generated_otp = random.randint(100000, 999999)
        otp_expiry_time = datetime.datetime.now(pytz.utc) + datetime.timedelta(minutes=3)
        user_instance = AccountsUserModel.objects.create(
            # username=validated_data["username"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            email=validated_data["email"],
            company=company_instance,
            # company_website = validated_data["company_website"],
            # user_type = "EMPLOYER",
            phone_number=validated_data["phone_number"],
            is_admin=True,
            otp=generated_otp,
            password = validated_data["password"],
            otp_expired_time=otp_expiry_time,
        )
        user_instance.set_password(validated_data["password"])
        user_instance.user_type = "ADMIN"
        # user_instance.password = crypt_password(validated_data["password"])
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
        return validated_data
    



class AdminAuthenticationVerifyOtpSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    # is_activating = serializers.BooleanField(required=True)

    logger = logging.LoggerAdapter(
        admin_flow_logger, {"app_name": "AdminAuthenticationVerifyOtpSerializer"}
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
            "FRONTEND_URL" : f"{UI_HOST}/auth/login?user_type=ADMIN",
            "username" : user_instance.username
        }
        message = render_to_string("auth/AdminSignUpAfterOTPVerified.html", context)
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
    

class CndidateUserResumeSerializer(serializers.ModelSerializer):
    """
    Serializer to represent the complete resume data.
    """

    class Meta:
        model = AccountsUserResumeModel
        fields = "__all__"


class AccountsUserResumeSerializer(serializers.ModelSerializer):
    """
    Serializer to represent the complete resume data.
    """

    class Meta:
        model = AccountsUserResumeModel
        fields = "__all__"

        
class AccountsUserJobHistorySerializer(serializers.ModelSerializer):
    """
    Serializer to represent the complete resume data.
    """

    class Meta:
        model = AccountsApplyJobHistoryModel
        fields = "__all__"

class AdminClientGETCandidateDetailsSerializer(serializers.ModelSerializer):
    """
    Serializer to represent the candidate details and application info.
    """
    candidate_id = serializers.CharField(source="candidate.id", read_only=True)
    candidate_user_id = serializers.CharField(source="candidate.user_id", read_only=True)
    candidate_first_name = serializers.CharField(source="candidate.first_name", read_only=True)
    candidate_last_name = serializers.CharField(source="candidate.last_name", read_only=True)
    candidate_username = serializers.CharField(source="candidate.username", read_only=True)
    candidate_email = serializers.CharField(source="candidate.email", read_only=True)
    candidate_profile_picture = serializers.CharField(source="candidate.profile_picture", read_only=True)
    candidate_country_code = serializers.CharField(source="candidate.country_code", read_only=True)
    candidate_phone_number = serializers.CharField(source="candidate.phone_number", read_only=True)
    candidate_short_name = serializers.CharField(source="candidate.short_name", read_only=True)
    candidate_user_type = serializers.CharField(source="candidate.user_type", read_only=True)
    candidate_linkedin_url = serializers.CharField(source="candidate.linkedin_url", read_only=True)
    candidate_timezone_info = serializers.CharField(source="candidate.timezone_info", read_only=True)
    candidate_user_skills = serializers.CharField(source="candidate.user_skills", read_only=True)

    applied_on = serializers.DateTimeField(source="created_at", read_only=True)
    resume_details = serializers.SerializerMethodField()

    logger = logging.LoggerAdapter(
        admin_flow_logger, {"app_name": "AdminClientGETCandidateDetailsSerializer"}
    )

    class Meta:
        model = AccountsApplyJobHistoryModel
        fields = [
            "candidate_id",
            "candidate_user_id",
            "candidate_first_name",
            "candidate_last_name",
            "candidate_username",
            "candidate_email",
            "candidate_profile_picture",
            "candidate_country_code",
            "candidate_phone_number",
            "candidate_short_name",
            "candidate_user_type",
            "current_designation",
            "candidate_linkedin_url",
            "candidate_timezone_info",
            "candidate_user_skills",
            "available_to_join",
            "promoted_by",
            "resume_details",
            "location",
            "applied_on",
            "experience_in_years",
            "experience_in_months",
            "cover_letter",
        ]

    def get_resume_details(self, obj):
        """
        Retrieves the resume data associated with the job application.
        """
        if obj.resume:
            return AccountsUserResumeSerializer(obj.resume).data
        return None


  
class AdminDashboardManageApplicantsSerializer(serializers.ModelSerializer):
    applicant_name = serializers.SerializerMethodField()
    applicant_id = serializers.SerializerMethodField()
    jobs_applied = serializers.IntegerField(source="jobs_applied_count", read_only=True)
    cv = serializers.CharField(read_only=True)
    resume_id = serializers.SerializerMethodField()

    class Meta:
        model = AccountsUserModel
        fields = ["id", "applicant_name", "jobs_applied", "cv","applicant_id","resume_id"]

    def get_applicant_name(self, obj):
        return f"{obj.first_name or ''} {obj.last_name or ''}".strip() or "No Name"
    
    def get_applicant_id(self,obj):
        return obj.id if obj.id else None
    
    def get_resume_id(self, obj):
        """Fetch resume ID for the applicant"""
        resume = AccountsUserResumeModel.objects.filter(candidate=obj).first()
        return resume.id if resume else None
    
class AdminDashboardManageClientsSerializer(serializers.ModelSerializer):
    job_count = serializers.IntegerField(read_only=True)
    applicant_count = serializers.IntegerField(read_only=True)
    title = serializers.CharField(source='company.title', read_only=True)
    
    class Meta:
        model = AccountsUserModel  # Changed to AccountsUserModel
        fields = [
            'id', 
            'email',
            'first_name',
            'last_name',
            'title',
            'job_count', 
            'applicant_count',
            'is_active'
        ]





class AdminGetClientUserProfileInfoSerializer(serializers.ModelSerializer):
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


class AdminClientDeleteCompanySerializer(serializers.Serializer):
    """
        DELETE functionality to delete existing job's
    """
    id = serializers.UUIDField(required = True)

    queryset = CompanyDetailModel.objects.all()
    
    INCORRECT_JOB_ID = COMPANY_EXISTS_MESSAGE

    logger = logging.LoggerAdapter(
        admin_flow_logger,{"app_name":"AdminClientDeleteCompanySerializer"}
    )

    def validate(self, data):
        company_id = data.get("id")

        if not CompanyDetailModel.objects.filter(id = company_id).exists():
            raise serializers.ValidationError(self.INCORRECT_JOB_ID)
        
        return data
    
    def create(self, validated_data):
        return_data = validated_data.copy()
        pk = validated_data.pop("id")
        with transaction.atomic():
            self.queryset.filter(pk=pk).delete(**validated_data)
        return return_data
    

class AdminManageClientUserProfileUpdateSerializer(serializers.ModelSerializer):
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
            "company_profile_picture",
            "is_active"
        ]

    def validate(self, data):
        company = data.get("company")
        company_website = data.get("company_website")

        if not AccountsUserModel.objects.filter(pk=data['id']).exists():
            raise serializers.ValidationError('Incorrect user ID')
        
        if is_filter_required("company_website", data):
            if CompanyDetailModel.objects.filter(company_website = company_website).exists():
                raise serializers.ValidationError("Company  with this website already exist's")
        return data

    def create(self, validated_data):
        with transaction.atomic():
            user = self.Meta.model.objects.select_related('company').get(pk=validated_data['id'])

            # Update user fields
            update_fields = {}
            for field in ['first_name', 'last_name', 'phone_number', 'country_code', 'profile_picture',"is_active"]:
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
                
            if "is_active" in validated_data and validated_data["is_active"] is False and user.company:
                user.company.is_active = False
                user.company.save()
                
                EmployerJobDetailsModel.objects.filter(
                    company=user.company
                ).update(is_active=False)

            if "is_active" in validated_data and validated_data["is_active"] is True and user.company:
                user.company.is_active = True
                user.company.save()
                
                EmployerJobDetailsModel.objects.filter(
                    company=user.company
                ).update(is_active=True)
        return validated_data