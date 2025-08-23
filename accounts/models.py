"""Models for auth app"""

import uuid
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager
)

from core.utils.enums import ApplyJobAboutThisJobTypeEnum, UserTypeEnum
from core.utils.generic_models import CoreGenericModel
from employer.models import CompanyDetailModel, EmployerJobDetailsModel
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models.signals import post_save
from django.contrib.postgres.fields import ArrayField


    

class CustomUserManager(BaseUserManager):
    """Custom user manager to create superuser or user"""

    def create_superuser(self, email, password):
        """for super user creation"""
        if email is None:
            raise ValueError("email")

        email = self.normalize_email(email)
        user = self.model(email=email)
        user.is_superuser = True
        user.is_active = True
        user.is_staff = True
        user.user_type = "ADMIN"
        user.first_name = "Admin"
        user.last_name = "Job Board"
        user.set_password(password)

        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """for user creation"""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password is not None:
            user.set_password(password)
        user.save(using=self._db)
        return user
    

# class AccountsRoleModel(CoreGenericModel):
#     id = models.UUIDField(default=uuid.uuid1, unique=True, primary_key=True, editable=False)
#     role_name = models.CharField(max_length=100, null=False, blank=True)
#     short_name = models.CharField(max_length=100, null=False, blank=True)

#     is_default = models.BooleanField(default=False)
#     is_editable = models.BooleanField(default=True)

#     class Meta:
#         db_table = "ROLES"
#         ordering = ("-created_at",)

#     def __str__(self):
#         return str(self.role_name)

class AccountsUserModel(AbstractBaseUser, PermissionsMixin, CoreGenericModel):
    """User model"""
    id = models.UUIDField(default=uuid.uuid1, unique=True, primary_key=True, editable=False)
    user_id = models.CharField(max_length=200, null=True, blank=True)
    username = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(blank=True, max_length=255, null=True, unique=True)
    profile_picture = models.TextField(null=True, blank=True)
    country_code = models.CharField(max_length=20, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    short_name = models.CharField(max_length=100, null=True, blank=True)
    # experience = models.CharField(
    #     max_length=255,
    #     null=True,
    #     blank=True
    # )
    # custom_password = models.CharField(max_length=256, null=True, blank=True)
    company = models.ForeignKey(
        CompanyDetailModel,
        on_delete=models.CASCADE,
        related_name="UserModel_company",
        null=True,
        blank=True,
    )
    # role = models.ForeignKey(
    #     AccountsRoleModel,
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True
    # )
    last_login = models.DateTimeField(null=True, blank=True)
    timezone_info = models.CharField(max_length=50, null=True, blank=True)
    linkedin_url = models.CharField(max_length=255, null=True, blank=True)

    otp = models.CharField(max_length=100, null=True, blank=True)
    otp_expired_time = models.DateTimeField(null=True, blank=True)
    user_type = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        choices=UserTypeEnum.choices(),
    )
    designation = models.CharField(
        max_length= 500,
        null=True,
        blank=True
    )
    user_skills = models.TextField(
        null=True,
        blank=True,
    )
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    USERNAME_FIELD = "email"

    objects = CustomUserManager()

    class Meta:
        db_table = "USERS"

    def __str__(self):
        return str(self.email)

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True
    

class AccountsUserResumeModel(
    CoreGenericModel
):
    id = models.UUIDField(default=uuid.uuid1, unique=True, primary_key=True, editable=False)
    name = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    first_name = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    last_name = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    title = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    date_of_birth = models.DateField(null=True,blank=True)
    phone_number = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )
    country_code = models.CharField(max_length=255,null=True,blank=True)
    email = models.EmailField(blank=True, max_length=255, null=True)
    address = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    professional_summary = models.TextField(null=True,blank=True)
    social_media_links = models.JSONField(
        null=True,
        blank=True
    )
    github = models.TextField(null=True,blank=True)
    portfolio = models.TextField(
        null=True,
        blank=True
    )
    education = ArrayField(models.JSONField(),null=True,blank=True)

    work_experience = ArrayField(models.JSONField(),null=True,blank=True)
    soft_skills = ArrayField(models.TextField(),null=True,blank=True)
    technical_skills = ArrayField(models.TextField(),null=True,blank=True)
    spoken_languages = ArrayField(models.TextField(),null=True,blank=True)
    projects = ArrayField(models.JSONField(),null=True,blank=True)
    awards = ArrayField(models.TextField(),null=True,blank=True)
    certifications = models.JSONField(null=True, blank=True)
    other_achievements = models.JSONField(null=True,blank=True)
    ml_report = models.JSONField(null=True,blank=True)
    cv = models.TextField(null=True,blank=True)
    company_id = models.ForeignKey(
        CompanyDetailModel,
        null=True,
        blank=True,
        related_name="AccountsUserResumeModel_company_id",
        on_delete=models.SET_NULL
    )
    job_id = models.ForeignKey(
        "employer.EmployerJobDetailsModel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    candidate = models.ForeignKey(
        AccountsUserModel,
        on_delete=models.CASCADE,
        related_name="AccountsUserResumeModel_candidate_id",
        null=True,
        blank=True,
    )
    parent_email = models.EmailField(null=True,
        blank=True,
        unique=True
    )
    resume_parser_data = models.JSONField(
        null=True,
        blank=True
    )
    is_cv_parsed = models.BooleanField(
        null=True,
        blank=True,
        default=False
    )
    cv_score = models.IntegerField(
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        AccountsUserModel,
        on_delete=models.CASCADE,
        related_name="AccountsUserResumeModel_user",
        null=True,
        blank=True
    )
    # test_fels = models.IntegerField(default=0)

    class Meta:
        db_table = "RESUME"
        ordering = ("-created_at",)


class AccountsApplyJobHistoryModel(CoreGenericModel):
    """AccountsApplyJobHistoryModel"""
    id = models.UUIDField(default=uuid.uuid1, unique=True, primary_key=True, editable=False)
    current_designation = models.CharField(
        max_length=500,
        null=True,
        blank=True
    )
    location = models.JSONField(
        null=True,
        blank=True
    )
    available_to_join = models.IntegerField(null=True, blank=True)
    promoted_by = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=ApplyJobAboutThisJobTypeEnum.choices(),
    )
    resume = models.ForeignKey(
        AccountsUserResumeModel,
        on_delete=models.CASCADE,
        null=True,
        related_name="AccountsApplyJobHistoryModel_resume",
        blank=True
    )
    experience_in_years = models.IntegerField(null=True,blank=True)
    experience_in_months = models.IntegerField(null=True,blank=True)
    cover_letter = models.TextField(null=True,blank=True)
    cover_letter_text = models.CharField(null=True,blank=True)
    company = models.ForeignKey(
        CompanyDetailModel,
        blank=True,
        related_name="AccountsApplyJobHistoryModel_company",
        on_delete=models.CASCADE
    )
    candidate = models.ForeignKey(
        AccountsUserModel,
        related_name="AccountsApplyJobHistoryModel_candidate",
        on_delete=models.CASCADE,
        blank=True
    )
    job = models.ForeignKey(
        EmployerJobDetailsModel,
        related_name="AccountsApplyJobHistoryModel_job",
        on_delete = models.CASCADE,
        null=True,
        blank=True
    )
    cv_score = models.IntegerField(null=True,blank=True)
    ml_report = models.JSONField(null=True,blank=True)

    class Meta:
        db_table = "RESUME_HISTORY"
        ordering = ("-created_at",)

class AccountsBlacklistTokensModel(CoreGenericModel):
    """AccountsBlacklistTokensModel"""
    token = models.CharField(max_length=500)
    user = models.ForeignKey(
        AccountsUserModel, related_name="AccountsBlacklistTokensModel_user", on_delete=models.CASCADE
    )
    is_login = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    # model managers
    objects = models.Manager()

    class Meta:
        db_table = "BLACKLIST_TOKENS"
        unique_together = ("token", "user")
        verbose_name = "Blacklist Token Model"
        verbose_name_plural = "Blacklist Token Models"

class AccountsLoginAnalyticsModel(CoreGenericModel):
    """AccountsLoginAnalyticsModel"""
    ip_address = models.CharField(max_length=500, null=True, blank=True)
    user = models.ForeignKey(
        AccountsUserModel, on_delete=models.CASCADE, related_name="AccountsLoginAnalyticsModel_user"
    )
    login_count = models.IntegerField(default=0)
    device_name = models.CharField(max_length=500, null=True, blank=True)
    token = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        db_table = "LOGIN_ANALYTICS"
        verbose_name = "Login Analytics Model"
        verbose_name_plural = "Login Analytics Model"

class CountryMobileCodesModel(models.Model):
    """CountryMobileCodesModel"""
    country_name = models.CharField(max_length = 50)
    country_code = models.CharField(max_length = 20)
    timezone = models.CharField(max_length = 50)
    utc = models.CharField(max_length = 50)
    currency = models.CharField(max_length=50)

    class Meta:
        db_table = "COUNTRY_MOBILE_CODES"


class CandidateShortListedJobsModel(CoreGenericModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(AccountsUserModel, on_delete=models.CASCADE, related_name="CandidateShortListedJobsModel_user")
    job = models.ForeignKey(EmployerJobDetailsModel, on_delete=models.CASCADE, related_name="CandidateShortListedJobsModel_job")

    class Meta:
        db_table = "SHORTLISTED_JOB_HISTORY"
