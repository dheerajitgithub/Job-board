"""urls for employer.client"""

from django.urls import path,include
from candidate.client.v1.manage_candidate import views as candidate_mgt_views

urlpatterns = [
    path(
        "candidate-registration-api/",
        candidate_mgt_views.CandidateAuthenticationCandidateRegistrationCreateAPIView.as_view(),
        name="CandidateAuthenticationCandidateRegistrationCreateAPIView",
    ),
    path(
        "candidate-landing-page-job-list-api/",
        candidate_mgt_views.CandidateLandingPageJobListAPIView.as_view(),
        name = "CandidateLandingPageJobListAPIView"
    ),
    path(
        "upload-resume-api/",
        candidate_mgt_views.CandidateClientUploadCVAPIView.as_view(),
        name = "CandidateClientUploadCVAPIView"
    ),
    path(
        "candidate-profile-management-api/",
        candidate_mgt_views.CandidateUserProfileUpdateAPIView.as_view(),
        name="CandidateUserProfileUpdateAPIView",
    ),
    path(
        "candidate-resume-details-api/",
        candidate_mgt_views.CandidateClientResumeDetialsAPIView.as_view(),
        name="CandidateClientResumeDetialsAPIView",
    ),
    path(
        "candidate-applying-jobs-api/",
        candidate_mgt_views.CandidateApplyingForJobsAPIView.as_view(),
        name = "CandidateApplyingForJobsAPIView"
    ),
    path(
        "shortlist-jobs-api/",
        candidate_mgt_views.CandidateClientShortListJobAPIView.as_view(),
        name = "CandidateClientShortListJobAPIView"
    ),
    path(
        "applied-jobs-api/",
        candidate_mgt_views.CandidateClientAppliedJobsAPIView.as_view(),
        name = "CandidateClientAppliedJobsAPIView"
    ),
    path(
        "candidate-dashboard-api/",
        candidate_mgt_views.CandidateClientDashBoardAPIView.as_view(),
        name = "CandidateClientDashBoardAPIView"
    ),
    path(
        "candidate-similar-jobs-api/",
        candidate_mgt_views.CandidateClientSimilarJobsAPIView.as_view(),
        name = "CandidateClientSimilarJobsAPIView"
    ),
    path(
        "track-applicants-api/",
        candidate_mgt_views.CandidateClientReportsTrackApplicantJobApplyingLinkAPIView.as_view(),
        name="CandidateClientReportsTrackApplicantJobApplyingLinkAPIView"
    ),
]
