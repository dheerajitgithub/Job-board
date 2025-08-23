"""urls for employer.client"""

from django.urls import path,include
from employer.client.v1.Manage_jobs import views as manage_jobs_views

urlpatterns = [
    path(
        "create-job-api/",
        manage_jobs_views.EmployerClientManageJobsCreateJobsAPIView.as_view(),
        name = "EmployerClientManageJobsCreateJobsAPIView"
    ),
    path(
        "convert-file-to-url-api/",
        manage_jobs_views.EmpployerConvertFileToURLAPIView.as_view(),
        name="EmpployerConvertFileToURLAPIView",
    ),
    path(
        "manage-job-api/",
        manage_jobs_views.EmployerClientManageJobsAPIView.as_view(),
        name = "EmployerClientManageJobsAPIView"
    ),
    path(
        "job-detials-api/",
        manage_jobs_views.EmployerClientGetJobDetailsAPIView.as_view(),
        name = "EmployerClientGetJobDetailsAPIView"
    ),
    path(
        "job-description-parsing-api/",
        manage_jobs_views.EmployerClientJobDescriptionParsingAPIView.as_view(),
        name = "EmployerClientJobDescriptionParsingAPIView"
    ),
    path(
        "landing-page-job-list-api/",
        manage_jobs_views.EmployerClientLandingPageJobListAPIView.as_view(),
        name = "EmployerClientLandingPageJobListAPIView"
    ),
    path(
        "landing-page-stats-api/",
        manage_jobs_views.EmployerClientLandingPageStatsCountAPIView.as_view(),
        name = "EmployerClientLandingPageStatsCountAPIView"
    ),
    path(
        "get-applicant-list-api/",
        manage_jobs_views.EmployerClientApplicantListJobsAPIView.as_view(),
        name = "EmployerClientApplicantListJobsAPIView"
    ),
    path(
        "get-applicant-data-api/",
        manage_jobs_views.EmployerClientGETCandidateDetailsAPIView.as_view(),
        name = "EmployerClientGETCandidateDetailsAPIView"
    ),
    path(
        "get-top-applicants-list-api/",
        manage_jobs_views.EmployerConnectedNetworksTopCVScoreAPIView.as_view(),
        name = "EmployerConnectedNetworksTopCVScoreAPIView"
    ),
    path(
        "top-applicants-send-mail-api/",
        manage_jobs_views.EmployerClientTopApplicantsSendMailAPIView.as_view(),
        name = "EmployerClientTopApplicantsSendMailAPIView"
    ),
    path(
        "track-job-api/",
        manage_jobs_views.EmployerClientReportsTrackApplicantJobApplyingLinkAPIView.as_view(),
        name="EmployerClientReportsTrackApplicantJobApplyingLinkAPIView"
    ),
]

    path(
        "get-recent-jobs-api/",
        manage_jobs_views.EmployerClientGetRecentJobAPIView.as_view(),
        name = "EmployerClientGetRecentJobAPIView"
    ),
]