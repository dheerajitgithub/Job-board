"""urls for employer.client"""

from django.urls import path,include
from Admin_flow.client.v1.dashboard import views as admin_dashoard_views

urlpatterns = [
    path(
        "admin-registration-api/",
        admin_dashoard_views.AdminClientAdminRegistrationCreateAPIView.as_view(),
        name="AdminClientAdminRegistrationCreateAPIView",
    ),
    path(
        "verify-otp-admin-api/",
        admin_dashoard_views.AdminAuthenticationVerifyOtpAPIView.as_view(),
        name="AdminAuthenticationVerifyOtpSerializer",
    ),
    path(
        "admin-dashboard-company-posting-job-count-api/",
        admin_dashoard_views.AdminClientDashBoardNoOfJobPostedByCompanyAPIView.as_view(),
        name = "AdminClientDashBoardNoOfJobPostedByCompanyAPIView"
    ),
    path(
        "admin-dashboard-active-company-count-api/",
        admin_dashoard_views.AdminClientDashBoardActiveInactiveCompanyAPIView.as_view(),
        name = "AdminClientDashBoardActiveInactiveCompanyAPIView"
    ),
    path(
        "admin-dashboard-applicants-count-api/",
        admin_dashoard_views.AdminClientDashBoardApplicantsCountAPIView.as_view(),
        name = "AdminClientDashBoardApplicantsCountAPIView"
    ),
    path(
        "admin-dashboard-manage-clients-api/",
        admin_dashoard_views.AdminClientDashBoardManageClientsAPIView.as_view(),
        name = "AdminClientDashBoardManageClientsAPIView"
    ),
    path(
        "admin-dashboard-manage-applicants-api/",
        admin_dashoard_views.AdminClientDashBoardManageApplicantsAPIView.as_view(),
        name = "AdminClientDashBoardManageApplicantsAPIView"
    ),
    path(
        "admin-dashboard-get-applicants-data-api/",
        admin_dashoard_views.AdminDashboardClientGETCandidateDetailsAPIView.as_view(),
        name = "AdminDashboardClientGETCandidateDetailsAPIView"
    ),
    path(
        "admin-dashboard-get-clients-data-api/",
        admin_dashoard_views.AdminClientManageClientAuthenticationUpdateAPIView.as_view(),
        name = "AdminClientManageClientAuthenticationUpdateAPIView"
    ),
]
