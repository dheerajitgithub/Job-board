import uuid
import datetime
from django.db import models
# from django.contrib.auth import get_user_model
# from accounts.models import AccountsUserModel
# from accounts.models import AccountsUserModel
from core.utils.enums import JobSalaryPeriodTypeEnum, JobStatusTypeEnum, JobsJobTypeEnum, UserTypeEnum
from core.utils.generic_models import CoreGenericModel
from django.utils.timezone import now 
from django.contrib.postgres.fields import ArrayField
# Create your models here.
    

class CompanyDetailModel(CoreGenericModel):
    id = models.UUIDField(default=uuid.uuid1, unique=True, primary_key=True, editable=False)
    company_id = models.CharField(max_length=200, unique=True, null=True,blank=True)
    company_logo = models.TextField(null=True, blank=True)
    title = models.CharField(max_length=255, unique=True,null=True, blank=True)
    company_email = models.EmailField(max_length=255, null=True, blank=True)
    company_website = models.CharField(max_length=512, null=True, blank=True)
    country_code = models.CharField(max_length=20, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    jobs_count = models.IntegerField(default=0)
    profile_picture = models.TextField(null=True, blank=True)
    team_count = models.IntegerField(default=0)
    student_count = models.IntegerField(null=True, blank=True, default=0)
    psychometric_add_on_count = models.IntegerField(default=0)
    linkedin_url = models.TextField(null=True, blank=True)
    gmail_url = models.TextField(null=True, blank=True)
    time_zone = models.CharField(max_length=100, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    temp_referral_code=models.CharField(max_length=8,null=True, blank=True)
    user_type = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        choices=UserTypeEnum.choices(),
    )
    no_of_cv_parsed = models.IntegerField(default = 124293)
    cv_score = models.IntegerField(
        null=True,
        blank=True
    )
    no_of_psy_parsed = models.IntegerField(default = 28261)
    parsed_count_updated_time = models.DateTimeField(default=now, blank=True, null=True)
    is_parsed_count_updated = models.BooleanField(default = False)
    is_active = models.BooleanField(null=True, blank=True)
    created_by = models.ForeignKey(
        'accounts.AccountsUserModel',
        on_delete=models.SET_NULL,
        related_name="CompanyDetailModel_created_by",
        null=True,
        blank=True
    )
    updated_by = models.ForeignKey(
        'accounts.AccountsUserModel',
        on_delete=models.SET_NULL,
        related_name="CompanyDetailModel_updated_by",
        null=True,
        blank=True
    )
    def __str__(self):
        return str(self.title)
    

class EmployerJobDetailsModel(CoreGenericModel):
    """
        Model for job.
    """
    id = models.UUIDField(default=uuid.uuid1, unique=True, primary_key=True, editable=False)
    job_title = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    job_id = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )
    description = models.TextField(
        null=True,
        blank=True
    )
    location = models.JSONField(
        null=True,
        blank=True
    )
    hard_skills = ArrayField(models.TextField(),null=True,blank=True)
    soft_skills = ArrayField(models.TextField(),null=True,blank=True)
    key_skills = ArrayField(models.TextField(),null=True,blank=True)
    career_page_link = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    job_duration = models.IntegerField(null=True,blank=True)
    job_type = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        choices=JobsJobTypeEnum.choices(),
    )
    company = models.ForeignKey(
        CompanyDetailModel,
        related_name="EmployerJobDetailsModel_company",
        on_delete= models.CASCADE,
        null=True,
        blank=True
    )
    candidate_applied = models.ManyToManyField(
        "accounts.AccountsUserModel",
        related_name="EmployerJobDetailsModel_candidate_applied",
        blank = True,
        null=True
    )
    invited_candidates = models.ManyToManyField(
        "accounts.AccountsUserModel",
        related_name="EmployerJobDetailsModel_invited_candidates",
        blank = True,
    )
    job_status = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        choices=JobStatusTypeEnum.choices()
    )
    created_by = models.ForeignKey(
        'accounts.AccountsUserModel',
        on_delete=models.SET_NULL,
        related_name="EmployerJobDetailsModel_created_by",
        null=True,
        blank=True
    )
    updated_by = models.ForeignKey(
        'accounts.AccountsUserModel',
        on_delete=models.SET_NULL,
        related_name="EmployerJobDetailsModel_updated_by",
        null=True,
        blank=True
    )
    salary_currency = models.CharField(
        max_length=10,
        null=True,
        blank=True
    )
    salary_range_from = models.IntegerField(
        null=True,
        blank=True
    )
    salary_range_to = models.IntegerField(
        null=True,
        blank=True
    )
    salary_period = models.CharField(
        max_length=100,
        choices=JobSalaryPeriodTypeEnum.choices(),
        null=True,
        blank=True
    )
    hide_salary = models.BooleanField(
        default=False,
        null=True,
        blank=True
    )
    shortlisted_by = models.ManyToManyField(
       'accounts.AccountsUserModel',
        related_name="EmployerJobDetailsModel_shortlisted_by",
        null=True,
        blank=True
    )
    experience_from = models.IntegerField(
        null=True,
        blank=True
    )
    experience_to = models.IntegerField(
        null=True,
        blank=True
    )
    experience = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )
    no_of_openings = models.IntegerField(
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)
    is_edited = models.BooleanField(default=False)
    is_shortlisted = models.BooleanField(default=False)

    class Meta:
        db_table = "JOB_DETAIL"
        ordering = ("-created_at",)

    def __str__(self):
        return str(self.job_title)
    

class EmployerTrackerModel(CoreGenericModel):
    id = models.UUIDField(default=uuid.uuid1, unique=True, primary_key=True, editable=False)
    browser = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )
    browser_version = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )
    os = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )
    os_version_string = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )
    device = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )
    device_brand = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )
    device_model = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )
    ip_address = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )
    candidate = models.ForeignKey(
        "accounts.AccountsUserModel",
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    company = models.ForeignKey(
        CompanyDetailModel,
        on_delete=models.CASCADE,
        related_name="EmployerTrackerModel_company",
        blank=True,
        null=True
    )
    job = models.ForeignKey(
        EmployerJobDetailsModel,
        on_delete=models.CASCADE,
        related_name="EmployerJobDetailsModel_job",
        blank=True,
        null=True
    )

    class Meta:
        db_table = "TRACKER"
        ordering = ("-created_at",)

    def __str__(self):
        return str(self.browser)