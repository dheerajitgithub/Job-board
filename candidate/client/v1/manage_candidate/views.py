import logging
from django.shortcuts import get_object_or_404
from rest_framework import generics,status, permissions
from rest_framework.response import Response
from rest_framework import views
from accounts import models
from accounts.authentication.v1.serializers import AccountsAuthenticationGetUserProfileInfoSerializer
from accounts.models import AccountsApplyJobHistoryModel, AccountsUserModel, AccountsUserResumeModel
from candidate.client.utils.cv_score import get_manual_skills, model_scoring
from candidate.client.utils.filterset_class import CandidateJobsDashboardModelFilterSet, DynamicPageSizePagination
from candidate.client.utils.parse_resume import save_resumes
from candidate.client.v1.manage_candidate.serializers import (
    CandidateAuthenticationCandidateRegistrationCreateSerializer,
    CandidateClientLandingPageJobListSerializer,
    CandidateClientReportsTrackApplicantJobApplyingLinkSerializer,
    CandidateEditCVDetailsSerializer,
    CandidateGetAppliedJobsCountSerializer,
    CandidateGetAppliesJobsListSerializer,
    CandidateResumeDetialsSerializer,
    CandidateShortListJobsCreateSerializer,
    CandidateShortListJobsListSerializer,
    CandidateShortListJobsUpdateSerializer,
    CandidateUploadCVPostSerializer,
    CandidateUserProfileUpdateSerializer,
    CandidatesApplyingJobSerializer,
    # CandidatesApplyingJobSerializer,
)
from core.utils.authentications import CustomAuthentication
from core.utils.generic_views import CoreGenericCustomPaginationAPIView, CoreGenericCustomPaginationPerPageAPIView, CoreGenericDeleteAPIView, CoreGenericGetAPIView, CoreGenericNonPaginatedFilterAPIView, CoreGenericPostAPIView, CoreGenericPutAPIView
from core.utils.utils import convert_blob_to_mp4, save_media
from employer.models import CompanyDetailModel, EmployerJobDetailsModel, EmployerTrackerModel
from core.settings import Exception_message
from core.settings import logger as candidate_mgt_logger
from core.utils.contants import (
    CANDIDATE_RESUME_SUCCESS_MESSAGE,
    CV_UPLOAD_SUCCESS_MESSAGE,
    EXCEPTION_MESSAGE,
    JOB_SUCCESS_MESSAGE,
    SHORTLIST_JOB_SUCCESS_MESSAGE,
    USER_PROFILE_SUCCESS_MESSAGE
)


class CandidateAuthenticationCandidateRegistrationCreateAPIView(
    CoreGenericPostAPIView,
    generics.GenericAPIView
):
    """
        POST Functionality for user registration form.
    """
    queryset = AccountsUserModel.objects.all()
    logger = logging.LoggerAdapter(
        candidate_mgt_logger, {"app_name": "CandidateAuthenticationCandidateRegistrationCreateAPIView"}
    )

    """ User Registraion API """
    def get_serializer_class(self):
        """
        Return the serializer class dynamicaly w.r.t to API method.
        """
        serializer_class = {
            "POST": CandidateAuthenticationCandidateRegistrationCreateSerializer,
        }
        return serializer_class.get(self.request.method)
    

class CandidateApplyingForJobsAPIView(
    views.APIView
):
    """
        POST Functionality for candidate to apply for jobs.
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]
    serializer_class = CandidatesApplyingJobSerializer
    logger = logging.LoggerAdapter(
        candidate_mgt_logger,{"app_name":"CandidateApplyingForJobsAPIView"}
    )

    def post(self, request):
        try:
            data=request.data
        
            serializer = self.serializer_class(data=data, context={"request" : request})
            if serializer.is_valid():
                serializer.save()
                return Response({"message" : "Job Applied"}, status=status.HTTP_200_OK)
            else:
                print(serializer.errors)
                for key in serializer.errors.keys():
                    error = serializer.errors[key]
                    if type(error) == type([]):
                        error = error[0]
                    else:
                        error = serializer.errors
                return Response({"message" : error, "data" : serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.logger.info(f"External Applicant Applying For Job POST Exception, {str(e)}")
            return Response(
                {"data":str(e),"message": Exception_message},
                status=status.HTTP_400_BAD_REQUEST,
            )

from django.db.models import Q
from rest_framework import filters
import django_filters

class CandidateLandingPageJobListAPIView(
    CoreGenericCustomPaginationPerPageAPIView,
    generics.GenericAPIView
):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]

    queryset = EmployerJobDetailsModel.objects.all()
    pagination_class = DynamicPageSizePagination
    success_message = JOB_SUCCESS_MESSAGE

    filter_backends = [
        filters.SearchFilter,
        django_filters.rest_framework.DjangoFilterBackend
    ]
    filterset_class = CandidateJobsDashboardModelFilterSet
    search_fields = [
        "job_title",
        "company__title"
    ]
    logger = logging.LoggerAdapter(
        candidate_mgt_logger,{"app_name":"CandidateLandingPageJobListAPIView"}
    )

    JOB_SUCCESS_MESSAGE = JOB_SUCCESS_MESSAGE

    def get_queryset(self):
        request = self.request
        user = request.user
        params = self.request.GET.dict()

        # Apply filters and search
        queryset = self.queryset.filter(is_active=True).order_by("-created_at")
        search_term = params.get('search', '')
        if search_term:
            queryset = queryset.filter(
                Q(job_title__icontains=search_term) |
                Q(company__title__icontains=search_term)
            )

        filterset = self.filterset_class(self.request.GET, queryset=queryset)
        final_queryset = filterset.qs 
        return final_queryset  

    def get_serializer_class(self):
        """
            Return the serializer class dynamicaly w.r.t to API method.
        """
        serializer_class = {
            "GET" : CandidateClientLandingPageJobListSerializer,
        }
        return serializer_class.get(self.request.method)

class CandidateClientUploadCVAPIView(
    CoreGenericPostAPIView,
    CoreGenericPutAPIView,
    CoreGenericDeleteAPIView,
    generics.GenericAPIView
):
    """
        GET,DELETE,PUT Functionality for uploading candidate's cv.
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]

    success_message = CV_UPLOAD_SUCCESS_MESSAGE

    queryset = AccountsUserResumeModel.objects.all()
    
    logger = logging.LoggerAdapter(
        candidate_mgt_logger, {"app_name": "CandidateClientUploadCVAPIView"}
    )


    def get_serializer_class(self):
        """
        Return the serializer class dynamicaly w.r.t to API method.
        """
        serializer_class = {
            "POST" : CandidateUploadCVPostSerializer,
            "PUT" : CandidateEditCVDetailsSerializer,
            # "DELETE": EmployerManageJobsDeleteJobsSerializer,
            # "GET" : EmployerManageJobsGetJobsListSerializer,
        }
        return serializer_class.get(self.request.method)

class CandidateUserProfileUpdateAPIView(
    CoreGenericPutAPIView,
    CoreGenericNonPaginatedFilterAPIView,
    generics.GenericAPIView
):
    """
       PUT Functionality for Profile Management Page API
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]
   
    logger = logging.LoggerAdapter(
        candidate_mgt_logger, {"app_name": "CandidateUserProfileUpdateAPIView"}
    )
    queryset = AccountsUserModel.objects.all()
    many= False

    success_message = USER_PROFILE_SUCCESS_MESSAGE

    def get_object(self):
        """
        Returns the object the view is displaying.

        You may want to override this if you need to provide non-standard
        queryset lookups.  Eg if objects are referenced using multiple
        keyword arguments in the url conf.
        """
        queryset = self.filter_queryset(self.queryset.all())

        filter_kwargs = {self.lookup_field: self.request.user.pk}
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        return obj
    
    def get_queryset(self):
        return self.get_object()
    
    def get_serializer_class(self):
        """
        Return the serializer class dynamicaly w.r.t to API method.
        """
        serializer_class = {
            "PUT": CandidateUserProfileUpdateSerializer,
            "GET": AccountsAuthenticationGetUserProfileInfoSerializer
        }
        return serializer_class.get(self.request.method)

class CandidateClientResumeDetialsAPIView(
    CoreGenericGetAPIView,
    generics.GenericAPIView
):
    """
        GET Functionality for resume details of the candidate.
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]

    success_message = CANDIDATE_RESUME_SUCCESS_MESSAGE

    queryset = AccountsUserResumeModel.objects.all()
    
    logger = logging.LoggerAdapter(
        candidate_mgt_logger, {"app_name": "CandidateClientResumeDetialsAPIView"}
    )

    def get_queryset(self,data):
        id = data.get("id")
        queryset = self.queryset.filter(candidate__id = id).data
        return queryset
    
    def get_serializer_class(self):
        """
        Return the serializer class dynamicaly w.r.t to API method.
        """
        serializer_class = {
            "GET" : CandidateResumeDetialsSerializer,
        }
        return serializer_class.get(self.request.method)
    
    def get_queryset(self):
        """
        Returns a filtered queryset based on `candidate_id` and `job_id` from the request.
        """
        params = self.request.GET.dict()
        candidate_id = params.get("candidate_id")

        queryset = AccountsUserResumeModel.objects.filter(
            candidate__id=candidate_id
        ).select_related("candidate")
        return queryset

    def get_serializer_class(self):
        """
        Returns the serializer class dynamically.
        """
        return CandidateResumeDetialsSerializer

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests for fetching candidate application details.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {"results": serializer.data, "message": "Success"},
            status=status.HTTP_200_OK,
        )

class CandidateClientShortListJobAPIView(
    CoreGenericPostAPIView,
    CoreGenericPutAPIView,
    CoreGenericCustomPaginationAPIView,
    generics.GenericAPIView
):
    """
        POST,GET Functionality for shortlisting the job's.
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]

    success_message = SHORTLIST_JOB_SUCCESS_MESSAGE

    queryset = AccountsUserResumeModel.objects.all()
    
    logger = logging.LoggerAdapter(
        candidate_mgt_logger, {"app_name": "CandidateClientShortListJobAPIView"}
    )

    def get_queryset(self):
        request = self.request
        user = request.user

        shortlisted_jobs = EmployerJobDetailsModel.objects.filter(is_shortlisted=True, is_active=True)

        resume_instance = AccountsUserResumeModel.objects.filter(candidate=user).first()
        resume_parser_data = resume_instance.resume_parser_data if resume_instance else {}

        for job in shortlisted_jobs:
            job_data = {
                "jobtitle": job.job_title,
                "location": job.location,
                "employment_type": job.job_type,
                "no_of_openings": int(job.no_of_openings) if job.no_of_openings is not None else 0,
                "experience_min": int(job.experience_from) if job.experience_from is not None else 0,
                "experience_max": int(job.experience_to) if job.experience_to is not None else 0,
                "salary_currency": job.salary_currency,
                "salary_per": job.salary_period,
                "salary_max": int(job.salary_range_to) if job.salary_range_to is not None else 0,
                "jobdescription": job.description,
                "key_skills": job.key_skills,
                "hardskils": job.hard_skills,
                "softskills": job.soft_skills,
                "job_type": job.job_type,
                "manual_keyskills": get_manual_skills(job.hard_skills, job.soft_skills, job.key_skills),
            }

            ml_report = model_scoring(job=job_data, parsing_data=resume_parser_data)
            cv_score = round(ml_report.get("total_score", 0), 1)

            job.cv_score = cv_score 

        return shortlisted_jobs 

    def get_serializer_class(self):
        """
        Return the serializer class dynamicaly w.r.t to API method.
        """
        serializer_class = {
            "POST" : CandidateShortListJobsCreateSerializer,
            "PUT" : CandidateShortListJobsUpdateSerializer,
            "GET" : CandidateShortListJobsListSerializer,
        }
        return serializer_class.get(self.request.method)

class CandidateClientAppliedJobsAPIView(
    CoreGenericCustomPaginationAPIView,
    generics.GenericAPIView
):
    """
        GET Functionality to get all appplied job's.
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]
    queryset = EmployerJobDetailsModel.objects.all()
    success_message = SHORTLIST_JOB_SUCCESS_MESSAGE
    filter_backends = [
        filters.SearchFilter,
        django_filters.rest_framework.DjangoFilterBackend
    ]
    search_fields = [
        "company__title"
    ]
    
    logger = logging.LoggerAdapter(
        candidate_mgt_logger, {"app_name": "CandidateClientAppliedJobsAPIView"}
    )

    def get_queryset(self):
        request = self.request
        user = request.user

        applied_jobs = AccountsApplyJobHistoryModel.objects.filter(
            candidate=user, job__is_active=True
        ).select_related("job", "job__company")

        resume_instance = AccountsUserResumeModel.objects.filter(candidate=user).first()
    
        if not resume_instance:
            print("⚠️ No resume found for candidate")
            return applied_jobs
        
        resume_parser_data = resume_instance.resume_parser_data or {}
        # Loop through each applied job and compute CV score
        for applied_job in applied_jobs:
            job = applied_job.job
            print("job_title",job.job_title)
            job_data = {
                "jobtitle": job.job_title,
                "location": job.location,
                "employment_type": job.job_type,
                "no_of_openings": int(job.no_of_openings) if job.no_of_openings is not None else 0,
                "experience_min": int(job.experience_from) if job.experience_from is not None else 0,
                "experience_max": int(job.experience_to) if job.experience_to is not None else 0,
                "salary_currency": job.salary_currency,
                "salary_per": job.salary_period,
                "salary_max": int(job.salary_range_to) if job.salary_range_to is not None else 0,
                "jobdescription": job.description,
                "key_skills": job.key_skills,
                "hardskils": job.hard_skills,
                "softskills": job.soft_skills,
                "job_type": job.job_type,
                "manual_keyskills": get_manual_skills(job.hard_skills, job.soft_skills, job.key_skills),
            }

            ml_report = model_scoring(job=job_data, parsing_data=resume_parser_data)
            cv_score = round(ml_report.get("total_score", 0), 1)

            setattr(applied_job, "cv_score", cv_score)

        return applied_jobs  

    
    def get_serializer_class(self):
        """
        Return the serializer class dynamicaly w.r.t to API method.
        """
        serializer_class = {
            "GET" : CandidateGetAppliesJobsListSerializer,
        }
        return serializer_class.get(self.request.method)
class CandidateClientDashBoardAPIView(
    CoreGenericCustomPaginationAPIView,
    generics.GenericAPIView
):
    """
        GET Functionality to get all appplied job's.
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]

    success_message = SHORTLIST_JOB_SUCCESS_MESSAGE

    
    logger = logging.LoggerAdapter(
        candidate_mgt_logger, {"app_name": "CandidateClientDashBoardAPIView"}
    )

    def get(self, request, *args, **kwargs):
        user = request.user
        applied_jobs_count = AccountsApplyJobHistoryModel.objects.filter(candidate=request.user).count()
        company_viewed_cv_count = EmployerTrackerModel.objects.filter(candidate = request.user).count()
        try:
            resume = AccountsUserResumeModel.objects.get(candidate=user)
            resume_skills = set(resume.technical_skills or []) | set(resume.soft_skills or [])
        except AccountsUserResumeModel.DoesNotExist:
            resume_skills = set()

        # Fetch similar jobs based on skills
        similar_jobs_count = EmployerJobDetailsModel.objects.filter(
           Q(hard_skills__overlap=list(resume_skills)) |
            Q(soft_skills__overlap=list(resume_skills)) |
           Q(key_skills__overlap=list(resume_skills))
        ).count()
        
        return Response(
            {
                "applied_jobs_count": applied_jobs_count,
                "company_viewed_cv_count" : company_viewed_cv_count,
                "similar_jobs_count" : similar_jobs_count
            }
        )

class CandidateClientSimilarJobsAPIView(
    CoreGenericCustomPaginationAPIView,
    generics.GenericAPIView
):
    """
        GET Functionality to get all appplied job's.
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]

    success_message = SHORTLIST_JOB_SUCCESS_MESSAGE

    queryset = EmployerJobDetailsModel.objects.all()
    
    logger = logging.LoggerAdapter(
        candidate_mgt_logger, {"app_name": "CandidateClientSimilarJobsAPIView"}
    )
    
    def get_candidate_skills(self):
        """Get skills from both user profile and resume"""
        all_skills = set()

        # Get user profile skills
        if self.request.user.user_skills:
            user_skills = [skill.lower().strip() for skill in self.request.user.user_skills.split(',')]
            all_skills.update(user_skills)

        # Get skills from most recent resume
        latest_resume = AccountsUserResumeModel.objects.filter(
            candidate=self.request.user
        ).order_by('-created_at').first()

        if latest_resume and latest_resume.technical_skills:
            resume_skills = [skill.lower().strip() for skill in latest_resume.technical_skills]
            all_skills.update(resume_skills)

        return all_skills

    def get_job_skills(self, job):
        """Get all skills required for a job"""
        job_skills = set()

        # Combine all types of skills
        if job.hard_skills:
            job_skills.update(skill.lower().strip() for skill in job.hard_skills)
        if job.key_skills:
            job_skills.update(skill.lower().strip() for skill in job.key_skills)
        if job.soft_skills:
            job_skills.update(skill.lower().strip() for skill in job.soft_skills)

        return job_skills

    def get_queryset(self):
        """Get jobs that match candidate's designation or skills."""
        candidate_skills = self.get_candidate_skills()
        
        candidate_designation = self.request.user.designation.lower().strip() if self.request.user.designation else None

        if not candidate_skills and not candidate_designation:
            return EmployerJobDetailsModel.objects.none()

        active_jobs = EmployerJobDetailsModel.objects.filter(
            is_active=True
        ).exclude(
            candidate_applied=self.request.user
        )

        designation_jobs = active_jobs.filter(job_title__icontains=candidate_designation) if candidate_designation else EmployerJobDetailsModel.objects.none()

        matching_job_ids = []
        for job in active_jobs:
            job_skills = self.get_job_skills(job)
            if job_skills and candidate_skills.intersection(job_skills):
                matching_job_ids.append(job.id)

        skill_jobs = active_jobs.filter(id__in=matching_job_ids)

        final_jobs = designation_jobs | skill_jobs

        return final_jobs.distinct()



    def get_serializer_class(self):
        """Return appropriate serializer for GET method"""
        return CandidateGetAppliesJobsListSerializer

    def list(self, request, *args, **kwargs):
        """List all matching jobs"""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class CandidateClientReportsTrackApplicantJobApplyingLinkAPIView(
    CoreGenericGetAPIView,
    generics.GenericAPIView
):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]
    serializer_class = CandidateClientReportsTrackApplicantJobApplyingLinkSerializer
    
    logger = logging.LoggerAdapter(
        candidate_mgt_logger, {"app_name": "CandidateClientReportsTrackApplicantJobApplyingLinkAPIView"}
    )
    
    def get_serializer_class(self):
        """
        Return the serializer class dynamicaly w.r.t to API method.
        """
        serializer_class = {
            "GET" : CandidateClientReportsTrackApplicantJobApplyingLinkSerializer,
        }
        return serializer_class.get(self.request.method)