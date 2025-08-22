"""Admin Config for Accounts.models"""


from django.contrib import admin
from .models import (
    # CustomUserManager,
    # AccountsRoleModel,
    AccountsApplyJobHistoryModel,
    AccountsUserModel,
    AccountsBlacklistTokensModel,
    AccountsLoginAnalyticsModel,
    AccountsUserResumeModel,
    CandidateShortListedJobsModel,
    CountryMobileCodesModel
)
# Register your models here.

@admin.register(AccountsUserModel)
class AccountsUserModelAdmin(admin.ModelAdmin):
    """user admin panel"""
    list_display = (
        "id",
        "username",
        "email",
        "user_type",
        "phone_number"
    )
    search_fields = (
        "id",
        "email",
        "phone_number"
    )
    list_filter = (
        "user_type",
    )

@admin.register(AccountsBlacklistTokensModel)
class AccountsBlacklistTokensAdmin(admin.ModelAdmin):
    """BlacklistTokensModel Panel config"""
    list_display = (
        "id",
        "user",
        "is_login"
        )
    search_fields = ("id", "is_login")
    list_filter = ("is_login",)

admin.site.register(AccountsLoginAnalyticsModel)

admin.site.register(CandidateShortListedJobsModel)

@admin.register(CountryMobileCodesModel)
class AccountsCountryMobileCodesAdmin(admin.ModelAdmin):
    """CountryMobileCodesModel Panel config"""
    list_display = (
        "id",
        "currency",
        )
    
@admin.register(AccountsUserResumeModel)
class AccountsCandidateResumeModelAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "company_id",
        "candidate_id",
        "is_cv_parsed",
        "cv_score",
    )

@admin.register(AccountsApplyJobHistoryModel)
class AccountsCandidateJobHistoryModelAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "resume",
        "company",
        "candidate",
        "job",
    )