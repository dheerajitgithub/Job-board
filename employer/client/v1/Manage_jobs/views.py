"""Views for employer.client"""

# from itertools import count

import logging
import django_filters
from rest_framework import generics, status,permissions, views, filters
from rest_framework.response import Response
from accounts.models import AccountsApplyJobHistoryModel, AccountsUserResumeModel
from candidate.client.utils.cv_score import get_manual_skills, model_scoring
from core.utils.authentications import CustomAuthentication
from core.utils.contants import EXCEPTION_MESSAGE, JOB_INSTANCE_MESSAGE, JOB_SUCCESS_MESSAGE, MAIL_SEND_SUCCESS_MESSAGE, PROFILE_PICTURE_SUCCESS_MESSAGE
from core.utils.paginators import get_paginated_data
from core.utils.generic_views import (
    CoreGenericCustomPaginationAPIView,
    CoreGenericDeleteAPIView,
    CoreGenericGetAPIView,
    CoreGenericPostAPIView,
    CoreGenericPutAPIView,
)
from core.settings import logger as employer_mgt_logger
from employer.client.v1.Manage_jobs.serializers import (
    EmployerClientCreateJobSerializer,
    EmployerClientGETCandidateDetailsSerializer,
    EmployerClientGetAppliedAplicantListSerializer,
    EmployerClientJobsParseJobDescriptionSerializer,
    EmployerClientLandingPageJobListSerializer,
    EmployerClientReportsTrackApplicantJobApplyingLinkSerializer,
    EmployerClientTopApplicantsSendMailSerializer,
    EmployerConvertFileToURLSerializer,
    EmployerManageJobsDeleteJobsSerializer,
    EmployerManageJobsGetJobsListSerializer,
    EmployerManageJobsGetSingleJobsDetailsSerializer,
    EmployerManageJobsUpdateJobsSerializer,
    # EmployerManageJobsGetJobsSerializer,
)
from employer.models import EmployerJobDetailsModel, EmployerTrackerModel
from django.db.models import Count, Q, IntegerField, Value

class EmployerClientManageJobsCreateJobsAPIView(
    CoreGenericPostAPIView,
    generics.GenericAPIView
):
    """
        POST Functionality for posting job's.
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]
    queryset = EmployerJobDetailsModel.objects.all()

    logger = logging.LoggerAdapter(
        employer_mgt_logger, {"app_name": "EmployerClientManageJobsCreateJobsAPIView"}
    )

    """ User Registraion API """
    def get_serializer_class(self):
        """
        Return the serializer class dynamicaly w.r.t to API method.
        """
        serializer_class = {
            "POST": EmployerClientCreateJobSerializer,
        }
        return serializer_class.get(self.request.method)
    

class EmpployerConvertFileToURLAPIView(
    CoreGenericPostAPIView,
    generics.GenericAPIView
):
    """
       POST Functionality for converting file into azure url
    """
    logger = logging.LoggerAdapter(
        employer_mgt_logger, {"app_name": "EmpployerConvertFileToURLAPIView"}
    )
    
    success_message = PROFILE_PICTURE_SUCCESS_MESSAGE

    def get_serializer_class(self):
        """
        Return the serializer class dynamicaly w.r.t to API method.
        """
        serializer_class = {
            "POST" : EmployerConvertFileToURLSerializer,
        }
        return serializer_class.get(self.request.method)
    

class EmployerClientManageJobsAPIView(
    CoreGenericPutAPIView,
    CoreGenericDeleteAPIView,
    CoreGenericCustomPaginationAPIView,
    generics.GenericAPIView
):
    """
        GET,DELETE,PUT Functionality for managing the job's.
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]
    success_message = JOB_SUCCESS_MESSAGE

    queryset = EmployerJobDetailsModel.objects.all()
    logger = logging.LoggerAdapter(
        employer_mgt_logger, {"app_name": "EmployerClientManageJobsAPIView"}
    )
    filter_backends = [
        filters.SearchFilter,
        django_filters.rest_framework.DjangoFilterBackend
    ]
    search_fields = [
        "job_title",
    ]

    def get_queryset(self):
        params = self.request.GET.dict()
        company_id = params.get("company_id")
        
        if company_id:
            queryset = EmployerJobDetailsModel.objects.filter(company__id=company_id)
            search_term = params.get('search', '')
            
            if search_term:
                queryset = queryset.filter(Q(job_title__icontains=search_term))
                
            job_ids = list(queryset.values_list('id', flat=True))

            self.active_jobs_count = queryset.filter(is_active=True).count()
            self.total_jobs_count = queryset.count()
            
            # Count total applicants for all jobs in this company
            self.total_applicants_count = (
                AccountsApplyJobHistoryModel.objects.filter(job__id__in=job_ids).count()
            )
            
            return queryset
    
        return EmployerJobDetailsModel.objects.none()

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = request.GET.dict().get("page", 1)
        
        serializer = self.get_serializer(queryset, many=True)
        response = get_paginated_data(request=request, queryset=serializer.data, page=page)

        response["no_of_active_jobs"] = getattr(self, "active_jobs_count", 0)
        response["no_of_jobs"] = getattr(self, "total_jobs_count", 0)
        response["no_of_applicants"] = getattr(self, "total_applicants_count", 0)  # Fixed

        return Response(response, status=status.HTTP_200_OK)
        
    
    def get_serializer_class(self):
        """
        Return the serializer class dynamicaly w.r.t to API method.
        """
        serializer_class = {
            "PUT" : EmployerManageJobsUpdateJobsSerializer,
            "DELETE": EmployerManageJobsDeleteJobsSerializer,
            "GET" : EmployerManageJobsGetJobsListSerializer,
        }
        return serializer_class.get(self.request.method)

from django.utils.timezone import now

class EmployerClientGetJobDetailsAPIView(
    CoreGenericGetAPIView,
    generics.GenericAPIView
):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]
    success_message = JOB_INSTANCE_MESSAGE

    logger = logging.LoggerAdapter(
        employer_mgt_logger,{"app_name":"EmployerClientGetJobDetailsAPIView"}
    )
    def get_queryset(self):
        params = self.request.GET.dict()
        job_id = params.get("id")
        if job_id:
            return EmployerJobDetailsModel.objects.filter(id=job_id)
        return EmployerJobDetailsModel.objects.none()
    
    
    
    def get_serializer_class(self):
        """
        Return the serializer class dynamicaly w.r.t to API method.
        """
        serializer_class = {
            "GET" : EmployerManageJobsGetSingleJobsDetailsSerializer
        }
        return serializer_class.get(self.request.method)
    
    def get(self, request, *args, **kwargs):
        params = self.request.GET.dict()
        job_id = params.get("id")
        user = request.user
        candidate_viewed_cv_count = EmployerTrackerModel.objects.filter(job = job_id).count()
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

        job_instance = queryset.first()
        
        # Get the serializer class and then instantiate it
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data={'id': str(job_instance.id)}, context={'request': request})
        
        # Validate the data
        serializer.is_valid(raise_exception=True)
        
        # Get the processed data
        job_data = serializer.create(serializer.validated_data)

        # Add additional counts
        total_applicants_count = AccountsApplyJobHistoryModel.objects.filter(job=job_instance).count()
        days_since_creation = (now().date() - job_instance.created_at.date()).days
        
        job_data["total_applicants_count"] = total_applicants_count
        job_data["days_since_creation"] = days_since_creation
        job_data["candidate_viewed_count"] = candidate_viewed_cv_count

        return Response(job_data, status=status.HTTP_200_OK)
    
class EmployerClientJobDescriptionParsingAPIView(
    views.APIView
):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]

    logger = logging.LoggerAdapter(
        employer_mgt_logger,{"app_name":"EmployerClientJobDescriptionParsingAPIView"}
    )
    
    def post(self, request):
        """
        Parse the description of a job.
        """
        try:
            serializer = EmployerClientJobsParseJobDescriptionSerializer(
                data=request.data, context={"logger": self.logger}
            )
            if serializer.is_valid():
                return Response(
                    {"data": serializer.validated_data, "message": "Success"},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.logger.info(f"Parse the description of a job API Exception, {str(e)}")
            return Response(
                {"data":str(e),"message": EXCEPTION_MESSAGE},
                status=status.HTTP_400_BAD_REQUEST,
            )


class EmployerClientLandingPageJobListAPIView(
    CoreGenericCustomPaginationAPIView,
    generics.GenericAPIView
):
    # permission_classes = [permissions.IsAuthenticated]
    # authentication_classes = [CustomAuthentication]
    queryset = EmployerJobDetailsModel.objects.all()
    success_message = JOB_SUCCESS_MESSAGE

    logger = logging.LoggerAdapter(
        employer_mgt_logger,{"app_name":"EmployerClientLandingPageJobListAPIView"}
    )

    filter_backends = [
        filters.SearchFilter,
        django_filters.rest_framework.DjangoFilterBackend
    ]
    # filterset_class = EmployerManageJobsModelFilterSet
    search_fields = [
        "job_title",
    ]
    def get_queryset(self):
        params = self.request.GET.dict()
        queryset = self.queryset.filter(
            Q(company__is_active = True)).order_by("-created_at")
        search_term = params.get('search', '')
        if search_term:
            queryset = queryset.filter(
                Q(job_title__icontains = search_term)
            )
        # filterset = self.filterset_class(self.request.GET, queryset=queryset)
        # return filterset.qs
        return queryset

    def get_serializer_class(self):
        """
            Return the serializer class dynamicaly w.r.t to API method.
        """
        serializer_class = {
            "GET" : EmployerClientLandingPageJobListSerializer,
        }

        return serializer_class.get(self.request.method)
    

class EmployerClientLandingPageStatsCountAPIView(
    generics.GenericAPIView
):
    logger = logging.LoggerAdapter(
        employer_mgt_logger,{"app_name":"EmployerClientLandingPageStatsCountAPIView"}
    )

    def get_queryset(self):
        return 
    

class EmployerClientApplicantListJobsAPIView(
    CoreGenericCustomPaginationAPIView,
    generics.GenericAPIView
):
    """
        GET Functionality to get all appplied candidate's.
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]

    success_message = JOB_INSTANCE_MESSAGE

    queryset = EmployerJobDetailsModel.objects.all()
    
    logger = logging.LoggerAdapter(
        employer_mgt_logger, {"app_name": "EmployerClientApplicantListJobsAPIView"}
    )

    def get_queryset(self):
        params = self.request.GET.dict()
        job_id = params.get("job_id")
        queryset = AccountsApplyJobHistoryModel.objects.filter(
            job__id=job_id
        ).select_related("candidate", "job")
        search_term = params.get('search', '')
        if search_term:
            queryset = queryset.filter(
                Q(candidate__username__icontains = search_term) 
                # Q(cv_score__icontains = search_term) 
            )
        return queryset
    
    def get_serializer_class(self):
        """
        Return the serializer class dynamicaly w.r.t to API method.
        """
        serializer_class = {
            "GET" : EmployerClientGetAppliedAplicantListSerializer,
        }
        return serializer_class.get(self.request.method)
    

class EmployerClientGETCandidateDetailsAPIView(
    CoreGenericGetAPIView,
    generics.GenericAPIView
):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]

    # queryset = AccountsUserResumeModel.objects.all()

    logger = logging.LoggerAdapter(
        employer_mgt_logger,{"app_name":"EmployerClientGETCandidateDetailsAPIView"}
    )
    

    def get_queryset(self):
        """
        Returns a filtered queryset based on `candidate_id` and `job_id` from the request.
        """
        params = self.request.GET.dict()
        job_id = params.get("job_id")
        candidate_id = params.get("candidate_id")

        if not job_id or not candidate_id:
            self.logger.error("Missing `job_id` or `candidate_id` in request parameters.")
            return AccountsApplyJobHistoryModel.objects.none()

        queryset = AccountsApplyJobHistoryModel.objects.filter(
            candidate__id=candidate_id, job__id=job_id
        ).select_related("candidate", "job", "resume")

        if not queryset.exists():
            self.logger.warning(f"No data found for job_id: {job_id}, candidate_id: {candidate_id}")

        return queryset

    def get_serializer_class(self):
        """
        Returns the serializer class dynamically.
        """
        return EmployerClientGETCandidateDetailsSerializer

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
    
class EmployerConnectedNetworksTopCVScoreAPIView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = [CustomAuthentication]
    api_logger = logging.LoggerAdapter(
        employer_mgt_logger, 
        {"app_name": "EmployerConnectedNetworksTopCVScoreAPIView"}
    )

    def prepare_job_dict(self, job):
        """Prepare job dictionary for scoring from PostgreSQL job model"""
        try:
            return {
                "jobtitle": job.job_title,
                "location": job.location,
                "employment_type": job.job_type,
                "no_of_openings": job.no_of_openings or 0,
                "experience_min": job.experience_from or 0,
                "experience_max": job.experience_to or 0,
                "salary_currency": job.salary_currency,
                "salary_per": job.salary_period,
                "salary_max": job.salary_range_to or 0,
                "jobdescription": job.description,
                "key_skills": job.key_skills or [],
                "hardskills": job.hard_skills,
                "softskills": job.soft_skills,
                "job_type": job.job_type,
                "manual_keyskills": get_manual_skills(job.hard_skills, job.soft_skills, job.key_skills),
            }
        except Exception as e:
            self.api_logger.error(f"Error preparing job dict: {str(e)}")
            return None

    def prepare_resume_data(self, resume):
        """Prepare resume data for response"""
        try:
            user = resume.candidate  
            first_name = user.first_name
            last_name = user.last_name
            return {
                "id": str(resume.id),
                "candidate_name": first_name +" " +  last_name,
                "candidate_email": resume.candidate.email,
                "current_designation": resume.title,
                "cv_score": resume.cv_score,
                "company_title": resume.company_id.title if resume.company_id else "",
                
            }
        except Exception as e:
            self.api_logger.error(f"Error preparing resume data: {str(e)}")
            return None

    def process_cv_data(self, resume, job_dict,job_instance):
        """Process individual resume data and calculate matching score"""
        try:
            # Calculate matching score using model_scoring
            model_dict = model_scoring(
                job=job_dict,
                parsing_data=resume.resume_parser_data or {}
            )
            user = resume.candidate  # Fetch latest user details
            first_name = user.first_name
            last_name = user.last_name

            is_invited = job_instance.invited_candidates.filter(id=resume.candidate.id).exists()
            if model_dict["total_score"] > 0:
                return {
                    "id": str(resume.id),
                    "candidate_name": first_name +" " +  last_name,
                    "candidate_email": resume.candidate.email,
                    "current_designation": resume.title,
                    "matching_score": model_dict["total_score"],
                    "score_breakdown": model_dict["scores_dict"],
                    "company_title": resume.company_id.title if resume.company_id else "",
                    "is_invited": is_invited
                }
            return None
        except Exception as e:
            self.api_logger.error(f"Error processing resume data: {str(e)}")
            return None

    def get(self, request):
        try:
            company = request.user.company
            params = request.GET.dict()
            job_id = params.get("job_id")

            if not job_id:
                return Response(
                    {"message": "Job ID is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                job = EmployerJobDetailsModel.objects.get(
                    id=job_id,
                    company=company,
                )
                self.api_logger.info(f"Found job with ID: {job_id}")
            except EmployerJobDetailsModel.DoesNotExist:
                return Response(
                    {"message": "Job not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            job_dict = self.prepare_job_dict(job)
            if not job_dict:
                return Response(
                    {"message": "Error preparing job data"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            base_query = AccountsUserResumeModel.objects.select_related('company_id')
            print("base_query", base_query.count())
            parsed_resumes = base_query.filter(is_cv_parsed=True)
            
            resumes_with_ml = parsed_resumes.filter(ml_report__isnull=False)
            
            # final_resumes = resumes_with_ml.exclude(candidate__in=job.candidate_applied.all())
            final_resumes = base_query

          

            final_list = []
            processed_count = 0
            failed_count = 0
            print("resume count", final_resumes.count())
            for resume in final_resumes:
                try:
                    processed_cv = self.process_cv_data(resume, job_dict,job)
                    if processed_cv:
                        final_list.append(processed_cv)
                        processed_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    self.api_logger.error(f"Error processing resume {resume.id}: {str(e)}")
                    failed_count += 1

            final_list.sort(key=lambda x: x["matching_score"], reverse=True)
            final_list = final_list[:10]

            return Response(
                {"message": final_list}, 
                status=status.HTTP_200_OK
            )

        except Exception as e:
            self.api_logger.error(f"CV Recommendations List API Exception: {str(e)}")
            return Response(
                {"message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
class EmployerClientTopApplicantsSendMailAPIView(
    CoreGenericPostAPIView,
    generics.GenericAPIView
):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]

    logger = logging.LoggerAdapter(
        employer_mgt_logger,{"app_name":"EmployerClientTopApplicantsSendMailAPIView"}
    )
    success_message = MAIL_SEND_SUCCESS_MESSAGE
    def get_serializer_class(self):
        """
            POST, Functionality for sending mails to top candidate's
        """
        serializer_class = {
            "POST" : EmployerClientTopApplicantsSendMailSerializer
        }
        return serializer_class.get(self.request.method)
    

class EmployerClientReportsTrackApplicantJobApplyingLinkAPIView(
    CoreGenericGetAPIView,
    generics.GenericAPIView
):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]
    serializer_class = EmployerClientReportsTrackApplicantJobApplyingLinkSerializer
    
    logger = logging.LoggerAdapter(
        employer_mgt_logger, {"app_name": "EmployerClientReportsTrackApplicantJobApplyingLinkAPIView"}
    )
    
    def get_serializer_class(self):
        """
        Return the serializer class dynamicaly w.r.t to API method.
        """
        serializer_class = {
            "GET" : EmployerClientReportsTrackApplicantJobApplyingLinkSerializer,
        }
        return serializer_class.get(self.request.method)
