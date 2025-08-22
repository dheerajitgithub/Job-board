from django.contrib import admin

from employer.models import CompanyDetailModel, EmployerJobDetailsModel, EmployerTrackerModel


@admin.register(CompanyDetailModel)
class EmployerCompanyDetailsModelAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
    )


@admin.register(EmployerJobDetailsModel)
class EmployerJobsModelAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "job_title",
        "job_id",
        "job_type",
        "job_status",
        "company",
        "is_active",
        "is_shortlisted"
    )
    search_fields = (
        "job_title",
        "job_type",
        'job_id'
    )
    list_filter =  (
        "job_type",
        "job_status",
        "company"
    )

admin.site.register(EmployerTrackerModel)
