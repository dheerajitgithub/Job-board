"""Serializer for accounts.authentication"""
import json
import string
import threading
import requests
import copy
import logging
import random
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings
from django.utils.translation import gettext as _
from django.template.loader import render_to_string
from django.db import transaction
from employer.client.utils.track import create_tracking_instance, is_already_tracking_date_saved
from core import settings
from core.settings import UI_HOST, logger as emlpoyer_mgt_logger
from core.utils.contants import (
    JOB_EXISTS_MESSAGE,
    COMPANY_EXISTS_MESSAGE
)
from core.utils.emails import send_an_email
from core.utils.utils import save_media
from accounts.models import (
    AccountsApplyJobHistoryModel,
    AccountsUserModel,
    AccountsUserResumeModel,
)
from employer.models import CompanyDetailModel, EmployerJobDetailsModel


jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
jwt_get_username_from_payload = api_settings.JWT_PAYLOAD_GET_USERNAME_HANDLER

api_logger = logging.LoggerAdapter(emlpoyer_mgt_logger,{"app_name":"accounts.authentication.v1.serializers"})

class EmployerClientCreateJobSerializer(serializers.ModelSerializer):
    """
        POST method for creating job.
    """
    job_title = serializers.CharField(required=True)
    job_type = serializers.CharField(required=True)
    experience_from = serializers.IntegerField(required=True)
    experience_to = serializers.IntegerField(required=True)
    company_id = serializers.UUIDField(required=True)
    key_skills = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    location = serializers.ListField(child=serializers.CharField(), required=True, write_only=True)
    description = serializers.CharField(required = True)

    logger = logging.LoggerAdapter(
        emlpoyer_mgt_logger,{"app_name": "EmployerClientCreateJobSerializer"}
    )
    queryset = EmployerJobDetailsModel.objects.all()
    class Meta:
        model = EmployerJobDetailsModel
        fields = "__all__"

    def validate(self, data):
        company_id = data.get("company_id")
        user = self.context['request'].user
        
        if user.user_type not in ['EMPLOYER', 'ADMIN']:
            raise serializers.ValidationError(
                "Only users with EMPLOYER or ADMIN access can create jobs"
            )
        
        if not CompanyDetailModel.objects.filter(id = company_id).exists():
            raise serializers.ValidationError(COMPANY_EXISTS_MESSAGE)
        
        return data
    
    def generate_job_id(self, company_name):
        """
        Generate a unique job ID based on the company's name and a random 4-digit number.
        """
        company_prefix = company_name[:3].upper()
        random_number = ''.join(random.choices(string.digits, k=4))
        job_id = f"{company_prefix}{random_number}"
        while EmployerJobDetailsModel.objects.filter(job_id=job_id).exists():
            random_number = ''.join(random.choices(string.digits, k=4))
            job_id = f"{company_prefix}{random_number}"
        return job_id

        
    def parse_job_description(self, description):
        """
        Parse job description using the dedicated serializer
        """
        serializer = EmployerClientJobsParseJobDescriptionSerializer(
            data={"description": description},
            context={"logger": self.logger}
        )
        try:
            serializer.is_valid(raise_exception=True)
            parsed_data = serializer.validated_data
            
            hard_skills = parsed_data.get("hard_skills", [])
            soft_skills = parsed_data.get("soft_skills", [])
            
            return hard_skills, soft_skills
        
        except serializers.ValidationError:
            self.logger.error("Job description parsing failed")
            return [], []
        
    def create(self, validated_data):
        """Create job function"""
        return_data = copy.deepcopy(validated_data)
        user = self.context["request"].user
        company_id = validated_data.pop("company_id", None)
        
        try:
            company_instance = CompanyDetailModel.objects.get(id=company_id)
        except CompanyDetailModel.DoesNotExist:
            raise serializers.ValidationError("Invalid company ID.")
        
        company_name = company_instance.title
        job_id = self.generate_job_id(company_name)
        
        validated_data['job_id'] = job_id

        key_skills = validated_data.pop("key_skills", [])
        description = validated_data.get("description", "")

        # 🔹 Call API to extract hard and soft skills from job description
        hard_skills, soft_skills = self.parse_job_description(description)

        combined_key_skills = list(set(key_skills + hard_skills))

        with transaction.atomic():
            job_instance = self.queryset.create(
                created_by=user,
                updated_by=user,
                company=company_instance,
                hard_skills=combined_key_skills,
                soft_skills=soft_skills,
                key_skills=combined_key_skills,
                **validated_data 
            )
            return_data = job_instance
            job_instance.save()
        
        return return_data

class EmployerConvertFileToURLSerializer(serializers.Serializer):
    """CompanyConvertFileToURLSerializer"""
    data = serializers.JSONField(required=False)

    logger = logging.LoggerAdapter(
        emlpoyer_mgt_logger, {"app_name": "EmployerConvertFileToURLSerializer"}
    )

    def validate(self, attrs):
        request = self.context["request"]
        if "file_fields" not in request.data:
            raise serializers.ValidationError("file_fields is required")
        return attrs

    def create(self, validated_data):
        """Creation company profile"""
        request = self.context["request"]
        url = save_media(request.data["file_fields"], path_req="job_board/")
        validated_data["data"] = url
        return validated_data

    def update(self, instance, validated_data):
        return (instance, validated_data)
    
from django.utils import timezone

class EmployerManageJobsUpdateJobsSerializer(
    serializers.ModelSerializer
):
    """
        Serializer for Updating job.
    """
    id = serializers.UUIDField(required=True)

    INCORRECT_ID_ERROR_MESSAGE =  JOB_EXISTS_MESSAGE

    logger = logging.LoggerAdapter(
        emlpoyer_mgt_logger, {"app_name": "EmployerManageJobsUpdateJobsSerializer"}
    )
    queryset = EmployerJobDetailsModel.objects.all()
    class Meta:
        model = EmployerJobDetailsModel
        fields = "__all__"

    def validate(self, data):
        user = self.context["request"].user

        if not self.queryset.filter(id = data["id"]).exists():
            raise serializers.ValidationError(self.INCORRECT_ID_ERROR_MESSAGE)

        if user.user_type not in  ["ADMIN","EMPLOYER"]:
            raise serializers.ValidationError("You do not have edit access for this comment")
        return data

    def create(self, validated_data):
        return_data = copy.deepcopy(validated_data)
        pk = validated_data.pop("id")
        with transaction.atomic():
            validated_data["is_edited"] = True
            validated_data["updated_at"] = timezone.now()  # Manually update the timestamp
            self.queryset.filter(id=pk).update(**validated_data)
        return return_data

class EmployerManageJobsDeleteJobsSerializer(serializers.Serializer):
    """
        DELETE functionality to delete existing job's
    """
    id = serializers.UUIDField(required = True)

    queryset = EmployerJobDetailsModel.objects.all()
    
    INCORRECT_JOB_ID = JOB_EXISTS_MESSAGE

    logger = logging.LoggerAdapter(
        emlpoyer_mgt_logger,{"app_name":"EmployerManageJobsDeleteJobsSerializer"}
    )

    def validate(self, data):
        job_id = data.get("id")

        if not EmployerJobDetailsModel.objects.filter(id = job_id).exists():
            raise serializers.ValidationError(self.INCORRECT_JOB_ID)
        
        return data
    
    def create(self, validated_data):
        return_data = validated_data.copy()
        pk = validated_data.pop("id")
        with transaction.atomic():
            self.queryset.filter(pk=pk).delete(**validated_data)
        return return_data
    


class EmployerManageJobsGetJobsListSerializer(serializers.ModelSerializer):
    candidate_applied_count = serializers.SerializerMethodField()
    total_applicants_count = serializers.SerializerMethodField()

    logger = logging.LoggerAdapter(
        emlpoyer_mgt_logger,{"app_name":"EmployerManageJobsGetJobsListSerializer"}
    )
    class Meta:
        model = EmployerJobDetailsModel
        fields = [
            "id",
            "job_title",
            "job_id",
            "description",
            "location",
            "hard_skills",
            "soft_skills",
            "total_applicants_count",
            "key_skills",
            "career_page_link",
            "job_duration",
            "job_type",
            "company",
            "candidate_applied_count",
            "invited_candidates",
            "job_status",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
            "salary_currency",
            "is_active",
            "salary_currency",
            "salary_range_from",
            "salary_range_to",
            "salary_period",
            "no_of_openings"
        ]

    def get_candidate_applied_count(self, obj):
        """Returns the number of candidates who applied for this job."""
        return obj.candidate_applied.count()

    def get_total_applicants_count(self, obj):
        """Returns the total applicants for this job from AccountsApplyJobHistoryModel."""
        return AccountsApplyJobHistoryModel.objects.filter(job_id=obj.id).count()


class EmployerJobDetailModelSerializer(serializers.ModelSerializer):
    company_title = serializers.CharField(source = "company.title",default = None)
    company_profile_picture = serializers.CharField(source = "company.profile_picture",default = None)
    is_candidate_applied = serializers.SerializerMethodField()



    class Meta:
        model = EmployerJobDetailsModel
        fields = [
            'id',
            'job_title',
            'job_id',
            'description',
            'location',
            'company_profile_picture',
            'company_title',
            'company',
            'hard_skills',
            'soft_skills',
            'key_skills',
            'career_page_link',
            'job_duration',
            'job_type',
            'job_status',
            'created_by',
            'updated_by',
            'salary_currency',
            'salary_range_from',
            'salary_range_to',
            'salary_period',
            'hide_salary',
            'experience_from',
            'experience_to',
            'experience',
            'no_of_openings',
            'is_active',
            'is_edited',
            "is_candidate_applied"
        ]
    def get_is_candidate_applied(self, obj):
        request = self.context.get('request')
        print("user",request.user)
        if request is None:
            return False 
        
        return AccountsApplyJobHistoryModel.objects.filter(candidate=request.user, job=obj).exists()
        
class EmployerManageJobsGetSingleJobsDetailsSerializer(serializers.Serializer):
    data = serializers.JSONField(required=False, read_only=True)
    is_applied = serializers.BooleanField(required=False, read_only=True)
    id = serializers.CharField(required=True)

    logger = logging.LoggerAdapter(
        emlpoyer_mgt_logger,{"app_name":"EmployerManageJobsGetJobsListSerializer"}
    )

    def validate(self, data):
        job_id = data.get("id")
        if not EmployerJobDetailsModel.objects.filter(id=job_id).exists():
            raise serializers.ValidationError(self.INCORRECT_JOB_ID)
        return data
    
    def create(self, validated_data):
        request = self.context["request"]
        job_id = validated_data.get("id")
        job_instance = EmployerJobDetailsModel.objects.get(id=job_id)
        
        is_applied = AccountsApplyJobHistoryModel.objects.filter(
            job=job_instance,
            candidate=request.user
        ).exists()
        
        data = EmployerJobDetailModelSerializer(
            job_instance,
            context={'request': request}
        ).data
        
        return {
            "id": job_id,
            "results": data,
            "is_applied": is_applied
        }

class EmployerClientJobsParseJobDescriptionSerializer(serializers.Serializer):
    description = serializers.CharField(required=True)

    def validate(self, data):
        description = data["description"]
        url = f"{settings.ML_HOST}jobparsing/"
        payload = json.dumps({"jobdescription": description})
        headers = {"Content-Type": "application/json"}
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            self.context["logger"].info("Job description successfully parsed")
        else:
            self.context["logger"].info("Job description parsing failed")
        parsed_data = response.json()["data"]
        return parsed_data
    

class EmployerClientLandingPageJobListSerializer(
    serializers.ModelSerializer
):
    company_title = serializers.CharField(source = "company.title",default=None)
    company_picture = serializers.CharField(source = "company.profile_picture",default=None)

    class Meta:
        model = EmployerJobDetailsModel
        fields = [
            "id",
            "job_title",
            "job_id",
            "location",
            "key_skills",
            "career_page_link",
            "job_duration",
            "company_picture",
            "job_type",
            "company",
            "company_title",
            "job_status",
            "created_by",
            "updated_by",
            "salary_currency",
            "salary_range_from",
            "salary_period",
            "experience_from",
            "experience_to",
            "experience",
            "no_of_openings",
            "is_active"
        ]



# class EmployerClientGetAppliedAplicantListSerializer(
#     serializers.ModelSerializer
# ):
#     logger  = logging.LoggerAdapter(
#         emlpoyer_mgt_logger,{"app_name":"EmployerClientGetAppliedAplicantListSerializer"}
#     )

#     class Meta:
#         model = AccountsUserModel
#         fields = "__all__"

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

class EmployerClientGetAppliedAplicantListSerializer(serializers.ModelSerializer):
    """
    Serializer to represent the candidate details and application info.
    """
    candidate_id = serializers.CharField(source="candidate.id", read_only = True)
    candidate_user_id = serializers.CharField(source="candidate.user_id", read_only = True)
    candidate_first_name = serializers.CharField(source="candidate.first_name", read_only=True)
    candidate_last_name = serializers.CharField(source="candidate.last_name", read_only=True)
    candidate_username = serializers.CharField(source="candidate.username", read_only = True)
    candidate_email = serializers.CharField(source="candidate.email", read_only=True)
    candidate_profile_picture = serializers.CharField(source="candidate.profile_picture", read_only = True)
    candidate_country_code = serializers.CharField(source="candidate.country_code", read_only = True)
    candidate_phone_number = serializers.CharField(source="candidate.phone_number", read_only = True)
    candidate_short_name = serializers.CharField(source="candidate.short_name", read_only=True)
    candidate_user_type = serializers.CharField(source="candidate.user_type", read_only=True)
    candidate_linkedin_url = serializers.CharField(source="candidate.linkedin_url", read_only=True)
    candidate_timezone_info = serializers.CharField(source="candidate.timezone_info", read_only=True)
    candidate_user_skills = serializers.CharField(source="candidate.short_name", read_only=True)
    candidate_user_skills = serializers.CharField(source="candidate.short_name", read_only=True)
    job_id = serializers.CharField(source="job.job_id", read_only=True)

    applied_on = serializers.DateTimeField(source="created_at", read_only=True)

    resume_details = serializers.SerializerMethodField()
    resume_history = serializers.SerializerMethodField()

    logger  = logging.LoggerAdapter(
        emlpoyer_mgt_logger,{"app_name":"EmployerClientGetAppliedAplicantListSerializer"}
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
            "resume_history",
            "job_id",
            "location",
            "applied_on",
            "experience_in_years",
            "experience_in_months",
            "cover_letter",
        ]

    def get_resume_details(self, obj):
        """
        Retrieves the complete resume data of the candidate.
        """
        resume = obj.candidate.AccountsUserResumeModel_candidate_id.first()
        if resume:
            return AccountsUserResumeSerializer(resume).data
        return None 
    
    def get_resume_history(self, obj):
        """
        Retrieves the complete resume data of the candidate.
        """
        resume = obj.candidate.AccountsApplyJobHistoryModel_candidate.first()
        if resume:
            return AccountsUserJobHistorySerializer(resume).data
        return None 


class EmployerClientGETCandidateDetailsSerializer(serializers.ModelSerializer):
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

    job_id = serializers.CharField(source="job.id", read_only=True)
    applied_on = serializers.DateTimeField(source="created_at", read_only=True)
    resume_details = serializers.SerializerMethodField()

    logger = logging.LoggerAdapter(
        emlpoyer_mgt_logger, {"app_name": "EmployerClientGETCandidateDetailsSerializer"}
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
            "job_id",
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



class EmployerConectedNetworksTopCVScoreAPIView(
    serializers.ModelSerializer
):
    job_id = serializers.UUIDField(required=True)

    logger = logging.LoggerAdapter(
        emlpoyer_mgt_logger, {"app_name": "EmployerConectedNetworksTopCVScoreAPIView"}
    )

    def validate(self, data):
        job_id = data.get("job_id")
        if not EmployerJobDetailsModel.objects.filter(id = job_id).exists():
            raise serializers.ValidationError()
        return data
    

class EmployerClientTopApplicantsSendMailSerializer(
    serializers.Serializer
):
    
    email = serializers.CharField(required = True)
    job_id = serializers.UUIDField(required = True)

    logger = logging.LoggerAdapter(
        emlpoyer_mgt_logger,{"app_name" : "EmployerClientTopApplicantsSendMailSerializer"}
    )

    def validate(self, data):
        email = data.get("email")
        job_id = data.get("job_id")

        if not AccountsUserModel.objects.filter(email = email).exists():
            raise serializers.ValidationError("User withthis email does not exist's")
        
        user_instance = AccountsUserModel.objects.get(email=email.lower())
        job_instance = EmployerJobDetailsModel.objects.get(id=job_id)

        # Check if the user has already been invited
        if job_instance.invited_candidates.filter(id=user_instance.id).exists():
            raise serializers.ValidationError("User has already been invited for this job.")

        return data
    
    def create(self, validated_data):
        data = validated_data

        job_instance = EmployerJobDetailsModel.objects.get(id = data.get("job_id"))

        company_id = self.context["request"].user.company.company_id
        email = validated_data["email"]
        user_instance = AccountsUserModel.objects.get(
            email=data["email"].lower()
        )
        with transaction.atomic():
            job_title = job_instance.job_title
            job_type = job_instance.job_type.replace("_", " ").title()
            job_location = ", ".join(job_instance.location) if isinstance(job_instance.location, list) else job_instance.location
            job_details_url = f"https://jobboard.aptagrim.co/candidate/alljobs/{job_instance.id}"

            is_logged_in = self.context["request"].user.is_authenticated
            if is_logged_in:
                frontend_url = job_details_url  # Redirect directly to job details
            else:
                frontend_url = f"https://jobboard.aptagrim.co/auth/login/?next={job_details_url}"
            job_instance.invited_candidates.add(user_instance)
            
            context = {
                "job_id": job_instance.job_id,
                "company": self.context["request"].user.company.title,
                "applicant_name": str(email).split("@")[0],
                "team_member_name": self.context["request"].user.username,
                "company_id": company_id,
                "job_title": job_title,
                "job_type": job_type,
                "job_location": job_location,
                "FRONTEND_URL": frontend_url
            }
                
            message = render_to_string("auth/job_invite.html", context)
            thread=threading.Thread(
                target=send_an_email,
                kwargs={
                    "receiver_email":[user_instance.email],
                    "subject": "JobBoard | New job recommended!",
                    "body":message
                }
            )
            thread.start()
        return validated_data


# class EmployerClientReportsTrackApplicantJobApplyingLinkSerializer(serializers.Serializer):

#     def validate(self, data):
#         if is_already_tracking_date_saved(request=self.context['request']):
#             raise serializers.ValidationError("Already visited")
#         return data 
    
#     def create(self, validated_data):
#         request = self.context['request']
#         request_details = create_tracking_instance(request)
#         return validated_data


class EmployerClientReportsTrackApplicantJobApplyingLinkSerializer(
    serializers.Serializer
):
    logger  = logging.LoggerAdapter(
        emlpoyer_mgt_logger,{"app_name":"EmployerClientReportsTrackApplicantJobApplyingLinkSerializer"}
    )
    
    def validate(self, data):
        if is_already_tracking_date_saved(request=self.context['request']):
            raise serializers.ValidationError("Already visited")
        return data 
    
    def create(self, validated_data):
        request = self.context['request']
        request_details = create_tracking_instance(request)
        return validated_data