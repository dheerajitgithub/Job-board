"""serializer for candidate"""

import copy
from datetime import datetime
from venv import logger
from django.db import transaction
import random,pytz
import datetime
import logging
import threading
from rest_framework import serializers
from accounts.models import AccountsApplyJobHistoryModel, AccountsUserModel, AccountsUserResumeModel, CandidateShortListedJobsModel
from candidate.client.utils.cv_score import get_manual_skills, model_scoring
from candidate.client.utils.parse_resume import format_date_of_birth, format_ml_resume_data, resume_parser_ml, save_resumes
from candidate.client.utils.track import create_tracking_instance, is_already_tracking_date_saved
from core.utils.contants import JOB_EXISTS_MESSAGE
from core.utils.emails import send_an_email
from core.utils.utils import generate_alphanumeric_code
from employer.models import CompanyDetailModel, EmployerJobDetailsModel
from core.settings import UI_HOST, logger as candidate_mgt_logger
from django.template.loader import render_to_string


class CandidateAuthenticationCandidateRegistrationCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True)
    country_code = serializers.CharField(required=True)


    logger = logging.LoggerAdapter(
        candidate_mgt_logger, {"app_name": "CandidateAuthenticationCandidateRegistrationCreateSerializer"}
    )
    
    class Meta:
        model = AccountsUserModel
        fields = "__all__"

    def validate(self, data):
        user_queryset = AccountsUserModel.objects.all()
        error_list = []

        if user_queryset.filter(email = data["email"]).exists():
            error_list.append({"email": "Email already exist's"})
        
        if user_queryset.filter(phone_number=data["phone_number"],country_code=data["country_code"]).exists():
                error_list.append({"phone_number": "Phone number already exists for this country code"})
        
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
            otp=generated_otp,
            **validated_data,
            otp_expired_time=otp_expiry_time,
        )
        # if password:
        user_instance.set_password(validated_data["password"])
        user_instance.user_type = "CANDIDATE"
        
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
    
class CandidateClientLandingPageJobListSerializer(serializers.ModelSerializer):
    company_title = serializers.CharField(source="company.title", default=None)
    company_picture = serializers.CharField(source="company.profile_picture", default=None)
    cv_score = serializers.SerializerMethodField()
    is_shortlisted = serializers.SerializerMethodField()

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
            "is_shortlisted",
            "salary_period",
            "experience_from",
            "experience_to",
            "experience",
            "no_of_openings",
            "is_active",
            "created_at",
            "cv_score",
        ]

    def get_cv_score(self, obj):
        """Compute cv_score using model_scoring function"""
        request = self.context.get("request")
        if not request:
            return 0  # Ensure request is available

        user = request.user  # Get logged-in candidate

        resume_instance = AccountsUserResumeModel.objects.filter(candidate=user).first()
        resume_parser_data = resume_instance.resume_parser_data if resume_instance else {}

        if not resume_parser_data:
            return 0

        job_data = {
            "jobtitle": obj.job_title,
            "location": obj.location,
            "employment_type": obj.job_type,
            "no_of_openings": obj.no_of_openings or 0,
            "experience_min": obj.experience_from or 0,
            "experience_max": obj.experience_to or 0,
            "salary_currency": obj.salary_currency,
            "salary_per": obj.salary_period,
            "salary_max": obj.salary_range_to or 0,
            "jobdescription": obj.description,
            "key_skills": obj.key_skills,
            "hardskills": obj.hard_skills,
            "softskills": obj.soft_skills,
            "job_type": obj.job_type,
            "manual_keyskills": get_manual_skills(obj.hard_skills, obj.soft_skills, obj.key_skills),
        }

        # Calculate cv_score using model_scoring
        ml_report = model_scoring(job=job_data, parsing_data=resume_parser_data)
        return round(ml_report.get("total_score", 0), 1)

    def get_is_shortlisted(self, obj):
        user = self.context["request"].user
        return (CandidateShortListedJobsModel.objects.filter(user=user, job=obj).exists())
    

from django.utils import timezone

class CandidateAuthenticationVerifyOtpSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    # is_activating = serializers.BooleanField(required=True)

    logger = logging.LoggerAdapter(
        candidate_mgt_logger, {"app_name": "CandidateAuthenticationVerifyOtpSerializer"}
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
    # if validated_data["is_activating"]:
        user_instance.is_verified = True
        user_instance.is_active = True
        user_instance.save()
        # sending account activation email
        
        
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
    
class CandidateUploadCVPostSerializer(
    serializers.ModelSerializer
):
    resume=serializers.FileField(required=True)
    data = serializers.JSONField(required=False)
    # job_id=serializers.CharField(required=True)

    logger = logging.LoggerAdapter(
        candidate_mgt_logger, {"app_name": "CandidateUploadCVPostSerializer"}
    )
    
    class Meta:
        model = AccountsUserResumeModel
        fields = "__all__"

    def validate(self, data):
        request=self.context["request"]
        resume=request.FILES["resume"]
        file_extension = resume.name.split('.')[-1].lower()
        if file_extension not in ["pdf", "docx", "doc"]:
            raise serializers.ValidationError({"message":"CV must be in pdf, doc or docx file format"})
        user = request.user
        if AccountsUserResumeModel.objects.filter(user=user).exists():
            raise serializers.ValidationError({"message": "You have already uploaded a resume."})
        return data

    def create(self, validated_data):
        try:
            request = self.context["request"]
            resume = request.FILES["resume"]
            user = request.user.username
            
            file_url, file_name = save_resumes(user, resume, user)
            resume_data = resume_parser_ml(file_url)
            
            if resume_data:
                user_instance = request.user
                req_data = {
                    "cv": file_url,
                    "resume_parser_data": resume_data
                }
                gen_data = format_ml_resume_data(resume_data)

               
                try:
                    if "date_of_birth" in gen_data and gen_data["date_of_birth"]:
                        dob = format_date_of_birth(gen_data["date_of_birth"])
                        if dob is None:
                            raise serializers.ValidationError({
                                "message": f"Invalid date_of_birth format: {gen_data.get('date_of_birth')}. Expected YYYY-MM-DD."
                            })
                        gen_data["date_of_birth"] = dob
                    else:
                        gen_data["date_of_birth"] = None
                except ValueError as e:
                    raise serializers.ValidationError({
                        "message": "Invalid date_of_birth format. Expected YYYY-MM-DD."
                    })
                
                # serializable_data = {
                #     **req_data,
                #     "candidate_id": str(user_instance.id),
                #     **gen_data
                # }
                
                create_data = {
                    **req_data,
                    "candidate": user_instance,
                    **gen_data
                }
                
                data = AccountsUserResumeModel.objects.create(**create_data)
                serializable_data = {
                    **req_data,
                    "candidate_id": str(user_instance.id),
                    **gen_data,
                    "id" : data.id
                }
                
                validated_data["data"] = serializable_data
            else:
                raise serializers.ValidationError({"message": "Resume parsing failed"})
                
        except Exception as e:
            raise serializers.ValidationError(str(e))
            
        return validated_data
    

class ClientApplicantsEducationSerializer(serializers.Serializer):
    degree = serializers.CharField(required=True, allow_blank = True)
    major = serializers.CharField(required=True, allow_blank = True)
    achieved_marks = serializers.CharField(required=True, allow_blank = True)
    location = serializers.CharField(required=False, allow_blank=True)
    institute = serializers.CharField(required=True, allow_blank = True)
    start_date = serializers.CharField(required=True, allow_blank = True)
    end_date = serializers.CharField(required=True, allow_blank = True)


class ClientApplicantsWorkExperienceSerializer(serializers.Serializer):
    company_name = serializers.CharField(required=True, allow_blank = True)
    job_title = serializers.CharField(required=True, allow_blank = True)
    start_date = serializers.CharField(required=False, allow_blank = True)
    end_date = serializers.CharField(required=False, allow_blank = True)
    location = serializers.CharField(required=False, allow_blank = True)
    skills = serializers.ListField(required=True, allow_empty = True)
    responsibilities = serializers.CharField(required=True,allow_blank=True)

class ClientApplicantsProjectsSerializer(serializers.Serializer):
    title = serializers.CharField(required=True, allow_blank = True)
    description = serializers.CharField(required=False, allow_blank = True)
    project_skills = serializers.ListField(required=True, allow_empty = True)
    link = serializers.CharField(required=False, allow_blank = True)


class CandidateEditCVDetailsSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=True)
    first_name = serializers.CharField(required=False, allow_blank = True)
    last_name = serializers.CharField(required=False, allow_blank = True)
    title = serializers.CharField(required=False, allow_blank = True)
    date_of_birth = serializers.CharField(required=False, allow_blank = True, allow_null=True)
    country_code = serializers.CharField(required=False, allow_blank = True)
    phone_number = serializers.CharField(required=False, allow_blank = True)
    email = serializers.EmailField(required=True)
    address = serializers.CharField(required=False, allow_blank = True)
    professional_summary = serializers.CharField(required=False, allow_blank = True)
    social_media_links = serializers.JSONField(required=False, allow_null = True)
    github = serializers.CharField(required=False, allow_blank = True)
    portfolio = serializers.CharField(required=False, allow_blank = True)
    education = ClientApplicantsEducationSerializer(
        many=True, required=False)
    work_experience = ClientApplicantsWorkExperienceSerializer(
        many=True, required=False)
    soft_skills = serializers.ListField(required=True, allow_empty = True)
    technical_skills = serializers.ListField(required=True, allow_empty = True)
    spoken_languages = serializers.ListField(required=True, allow_empty = True)
    projects = ClientApplicantsProjectsSerializer(
        many=True, required=False)
    awards = serializers.ListField(required=False, allow_empty = True)
    certifications = serializers.ListField(required=False, allow_empty = True)
    other_achievements = serializers.ListField(required=False, allow_empty = True)

    logger = logging.LoggerAdapter(
        candidate_mgt_logger, {"app_name": "CandidateEditCVDetailsSerializer"}
    )
    class Meta:
        model = AccountsUserResumeModel
        fields = "__all__"


    def validate(self,data):
        id = data.get("id")
        if not AccountsUserResumeModel.objects.filter(id = id).exists():
            raise serializers.ValidationError("Cv with this ID does not exist's")
        return data

    
    def create(self, validated_data):
        initial_data = validated_data.copy()
        with transaction.atomic():
            candidate_id = validated_data.pop("id")
            candidate = self.Meta.model.objects.get(pk=candidate_id)

            self.Meta.model.objects.filter(pk=candidate.pk).update(**validated_data)
        return initial_data
    
class CandidateUserProfileUpdateSerializer(serializers.ModelSerializer):
    
    id = serializers.UUIDField()

    class Meta:
        model = AccountsUserModel
        fields = [
            "id",
            "first_name",
            "last_name",
            "phone_number",
            "country_code",
            "profile_picture",
            "linkedin_url"
        ]

    def validate(self, data):
        if not self.Meta.model.objects.filter(pk=data['id']).exists():
            raise serializers.ValidationError('Incorrect User ID')
        return data

    def create(self, validated_data):
        with transaction.atomic():
            user = self.Meta.model.objects.get(pk=validated_data['id'])
            
            update_fields = {}
            for field in ['first_name', 'last_name', 'phone_number', 'country_code', 'profile_picture',"linkedin_url"]:
                if field in validated_data:
                    update_fields[field] = validated_data[field]
            
            self.Meta.model.objects.filter(pk=user.pk).update(**update_fields)
            user.refresh_from_db()
        return user
    

from django.db.models import Q

class CandidatesApplyingJobSerializer(serializers.Serializer):
    job_id = serializers.CharField(required=True)
    company_id = serializers.CharField(required=True)
    name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    country_code = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True)
    location = serializers.CharField(required=True)
    available_to_join = serializers.CharField(required=True)
    experience_in_years = serializers.IntegerField(required=True)
    experience_in_months = serializers.IntegerField(required=True)
    profile = serializers.FileField(required=False)
    cover_letter = serializers.FileField(required=False)
    cover_letter_text = serializers.CharField(required=False)
    
    current_designation=serializers.CharField(required=True)
    promoted_by = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        request = self.context["request"]
        if not CompanyDetailModel.objects.filter(id=data.get("company_id")).exists():
            raise serializers.ValidationError("Company does not exist's")
        
        company = CompanyDetailModel.objects.get(id=data.get("company_id"))
        
        if not EmployerJobDetailsModel.objects.filter(id =data.get("job_id")).exists():
            raise serializers.ValidationError("Job does not exist's")
        
        if AccountsApplyJobHistoryModel.objects.filter(company=company,candidate= request.user,job__id = data.get("job_id")).exists():
            raise serializers.ValidationError("You have already applied for this job")

        return data
    

    def create(self, validated_data):
        request = self.context["request"]
        return_data = copy.deepcopy(validated_data)
        job_id = validated_data.pop("job_id", None)
        username = validated_data.pop("name")
        name_parts = username.split(maxsplit=1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        job_instance = EmployerJobDetailsModel.objects.get(id = job_id)
        resume_instance, _ = AccountsUserResumeModel.objects.get_or_create(candidate = request.user)

        with transaction.atomic():
            request.user.first_name = first_name
            request.user.last_name = last_name
            
            resume_instance.name = username
            resume_instance.first_name = first_name  # Optional: if your model has a first_name field
            resume_instance.last_name = last_name
            resume_instance.email = validated_data.pop("email")
            resume_instance.phone_number = validated_data.pop("phone_number")
            resume_instance.country_code = validated_data.pop("country_code")
            resume_instance.save()
            resume_history_instance = AccountsApplyJobHistoryModel.objects.all()
            if "cover_letter" in validated_data:
                if request.data["cover_letter"]:
                    cover_letter_url, file_name = save_resumes(company_name=str(username), file=request.FILES["cover_letter"],applicant_name= "")
                    
                    validated_data["cover_letter"] = cover_letter_url
            else:
                validated_data["cover_letter"] = ""


            job = {
                    "jobtitle": job_instance.job_title,
                    "location": job_instance.location,
                    "employment_type": job_instance.job_type,
                    "no_of_openings": int(job_instance.no_of_openings),
                    "experience_min": int(job_instance.experience_from),
                    "experience_max": int(job_instance.experience_to),
                    "salary_currency": job_instance.salary_currency,
                    "salary_per": job_instance.salary_period,
                    "salary_max": int(job_instance.salary_range_to),
                    "jobdescription": job_instance.description,
                    "key_skills": job_instance.key_skills,
                    "hardskils": job_instance.hard_skills,
                    "softskills": job_instance.soft_skills,
                    "job_type": job_instance.job_type,
                    "manual_keyskills": get_manual_skills(job_instance.hard_skills,job_instance.soft_skills,job_instance.key_skills)
                }
            ml_report = model_scoring(
                            job=job,
                            parsing_data=resume_instance.resume_parser_data,
                        )
            logger.info(f"ML report: {ml_report}")
            try:
                cv_score = ml_report["total_score"]
            except KeyError:
                cv_score = 0
            cv_score=round(cv_score,1)
            logger.info(f"CV score: {cv_score}")

            job_apply_instance = AccountsApplyJobHistoryModel.objects.create(candidate = request.user,
                                                             resume = resume_instance,
                                                             company = job_instance.company,
                                                             job = job_instance,
                                                             location = validated_data.get("location"),
                                                             current_designation = validated_data.get("current_designation"),
                                                             experience_in_years = validated_data.get("experience_in_years"),
                                                             experience_in_months = validated_data.get("experience_in_months"),
                                                             cover_letter = validated_data.get("cover_letter"),
                                                             available_to_join = int(validated_data.get("available_to_join")),
                                                             promoted_by = validated_data.get("promoted_by"),
                                                             ml_report = ml_report,
                                                             cv_score = cv_score
                                            )
            
            
            # job_new_instance = EmployerJobDetailsModel.objects.create(**job_instance)
            if "cover_letter_text" in validated_data:
                job_apply_instance.cover_letter_text = validated_data.get("cover_letter_text")
                job_apply_instance.save()

        return return_data
   

class CandidateShortListJobsCreateSerializer(
    serializers.ModelSerializer
):
    id = serializers.UUIDField(required=True)
    queryset = EmployerJobDetailsModel.objects.all()

    logger = logging.LoggerAdapter(
        candidate_mgt_logger,{"app_name":"CandidateShortListJobsCreateSerializer"}
    )
    class Meta:
        model = EmployerJobDetailsModel
        fields = [
            "id",
            "is_shortlisted"
        ]

    def validate(self, data):
        job_id = data.get("id")
        if not self.queryset.filter(id = job_id).exists():
            raise serializers.ValidationError(JOB_EXISTS_MESSAGE)
        return data 
    
    def create(self, validated_data):
        inital_data = validated_data.copy()
        user = self.context["request"].user
        job_id = validated_data.pop("id")
        is_shortlisted = validated_data.get("is_shortlisted",False)

        job_instance = EmployerJobDetailsModel.objects.get(id=job_id)
        with transaction.atomic():
            CandidateShortListedJobsModel.objects.get_or_create(user=user, job=job_instance)

        return inital_data
    

class CandidateShortListJobsUpdateSerializer(
    serializers.ModelSerializer
):
    id = serializers.UUIDField(required=True)
    queryset = EmployerJobDetailsModel.objects.all()

    logger = logging.LoggerAdapter(
        candidate_mgt_logger,{"app_name":"CandidateShortListJobsUpdateSerializer"}
    )
    class Meta:
        model = EmployerJobDetailsModel
        fields = [
            "id",
            "is_shortlisted"
        ]

    def validate(self, data):
        job_id = data.get("id")
        if not self.queryset.filter(id = job_id).exists():
            raise serializers.ValidationError(JOB_EXISTS_MESSAGE)
        return data 
    
    def create(self, validated_data):
        initial_data = validated_data.copy()
        user = self.context["request"].user
        job_id = validated_data.pop("id")
        is_shortlisted = validated_data.get("is_shortlisted", False)
        job_instance = EmployerJobDetailsModel.objects.get(id=job_id)
        with transaction.atomic():
            instance, _ = CandidateShortListedJobsModel.objects.get_or_create(user=user, job=job_instance)
            if not is_shortlisted:
                instance.delete()
        return initial_data

            
        
    
class CandidateShortListJobsListSerializer(
    serializers.ModelSerializer
):
    company_name = serializers.CharField(source = "company.title",read_only = True)
    profile_picture = serializers.CharField(source = "company.profile_picture",read_only = True)
    cv_score = serializers.SerializerMethodField() 
    # job_title /
    logger  = logging.LoggerAdapter(
        candidate_mgt_logger,{"app_name":"CandidateShortListJobsListSerializer"}
    )

    class Meta:
        model = EmployerJobDetailsModel
        fields = [
            "id",
            "job_id",
            "job_title",
            "location",
            "company_name",
            "company",
            "cv_score",
            "profile_picture",
            "created_at",
            "updated_at",
        ]

    def get_cv_score(self, obj):
        """
        Fetch the CV score from the queryset.
        """
        return getattr(obj, "cv_score", None) 

class AccountsUserResumeSerializer(serializers.ModelSerializer):
    """
    Serializer to represent the complete resume data.
    """

    class Meta:
        model = AccountsUserResumeModel
        fields = "__all__"

class CandidateResumeDetialsSerializer(serializers.ModelSerializer):
    """
    Serializer to represent the candidate details and application info.
    """
    # candidate_id = serializers.CharField(source="candidate.id", read_only=True)
    # candidate_user_id = serializers.CharField(source="candidate.user_id", read_only=True)
    # candidate_first_name = serializers.CharField(source="candidate.first_name", read_only=True)
    # candidate_last_name = serializers.CharField(source="candidate.last_name", read_only=True)
    # candidate_username = serializers.CharField(source="candidate.username", read_only=True)
    # candidate_email = serializers.CharField(source="candidate.email", read_only=True)
    # candidate_profile_picture = serializers.CharField(source="candidate.profile_picture", read_only=True)
    # candidate_country_code = serializers.CharField(source="candidate.country_code", read_only=True)
    # candidate_phone_number = serializers.CharField(source="candidate.phone_number", read_only=True)
    # candidate_short_name = serializers.CharField(source="candidate.short_name", read_only=True)
    # candidate_user_type = serializers.CharField(source="candidate.user_type", read_only=True)
    # candidate_linkedin_url = serializers.CharField(source="candidate.linkedin_url", read_only=True)
    # candidate_timezone_info = serializers.CharField(source="candidate.timezone_info", read_only=True)
    # candidate_user_skills = serializers.CharField(source="candidate.user_skills", read_only=True)

    # job_id = serializers.CharField(source="job.id", read_only=True)
    # applied_on = serializers.DateTimeField(source="created_at", read_only=True)
    # resume_details = serializers.SerializerMethodField()

    logger = logging.LoggerAdapter(
        candidate_mgt_logger, {"app_name": "CandidateResumeDetialsSerializer"}
    )

    class Meta:
        model = AccountsUserResumeModel
        fields = "__all__"

    # def get_resume_details(self, obj):
    #     """
    #     Retrieves the resume data associated with the job application.
    #     """
    #     if obj.resume:
    #         return AccountsUserResumeSerializer(obj.resume).data
    #     return None


class CandidateGetAppliesJobsListSerializer(
    serializers.ModelSerializer
):
    company_name = serializers.CharField(source = "company.title",read_only = True)
    job_title = serializers.CharField(source = "job.job_title",read_only = True)
    location = serializers.JSONField(source='job.location', read_only=True)
    job_id = serializers.CharField(source="job.job_id",read_only = True)
    applied_job_main_id = serializers.CharField(source="job.id",read_only=True)
    cv_score = serializers.SerializerMethodField()
    
    logger  = logging.LoggerAdapter(
        candidate_mgt_logger,{"app_name":"CandidateGetAppliesJobsListSerializer"}
    )

    class Meta:
        model = AccountsApplyJobHistoryModel
        fields = [
            "id",
            "job_id",
            "applied_job_main_id",
            "job_title",
            "location",
            "cv_score",
            "company_name",
            "company",
            "created_at",
            "updated_at"
        ]

    def get_cv_score(self, obj):
        """
        Fetch the latest CV score from the Resume model.
        """
        resume = AccountsUserResumeModel.objects.filter(candidate=obj.candidate).first()
        return resume.cv_score if resume else None



class CandidateGetAppliedJobsCountSerializer(
    serializers.Serializer
):
    logger  = logging.LoggerAdapter(
        candidate_mgt_logger,{"app_name":"CandidateGetAppliesJobsListSerializer"}
    )

    applied_jobs_count = serializers.IntegerField()

    def to_representation(self, instance):
        return {
            "applied_jobs_count": instance
        }



class CandidateClientReportsTrackApplicantJobApplyingLinkSerializer(
    serializers.Serializer
):
    logger  = logging.LoggerAdapter(
        candidate_mgt_logger,{"app_name":"CandidateClientReportsTrackApplicantJobApplyingLinkSerializer"}
    )
    
    def validate(self, data):
        if is_already_tracking_date_saved(request=self.context['request']):
            raise serializers.ValidationError("Already visited")
        return data 
    
    def create(self, validated_data):
        request = self.context['request']
        request_details = create_tracking_instance(request)
        return validated_data