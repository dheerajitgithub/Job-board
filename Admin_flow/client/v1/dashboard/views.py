import logging
from datetime import datetime
import django_filters
from django.db.models import Count, Sum, OuterRef, Subquery, Exists
from django.shortcuts import get_object_or_404
from rest_framework import generics,status, permissions, filters
from rest_framework.response import Response
from accounts.models import AccountsApplyJobHistoryModel, AccountsUserModel, AccountsUserResumeModel
from Admin_flow.client.v1.dashboard.serializers import AdminAuthenticationVerifyOtpSerializer, AdminClientAdminRegistrationCreateSerializer, AdminClientDeleteCompanySerializer, AdminClientGETCandidateDetailsSerializer, AdminDashboardManageApplicantsSerializer, AdminDashboardManageClientsSerializer, AdminGetClientUserProfileInfoSerializer, AdminManageClientUserProfileUpdateSerializer
from core.utils.authentications import CustomAuthentication
from core.utils.generic_views import CoreGenericCustomPaginationAPIView, CoreGenericDeleteAPIView, CoreGenericGetAPIView, CoreGenericNonPaginatedFilterAPIView, CoreGenericPostAPIView, CoreGenericPutAPIView
from core.utils.permissions import IsAdminUser
from employer.models import CompanyDetailModel
from core.settings import logger as admin_flow_logger
from core.utils.contants import (
    EXCEPTION_MESSAGE,
    SHORTLIST_JOB_SUCCESS_MESSAGE,
    USER_PROFILE_SUCCESS_MESSAGE,
)


class AdminClientAdminRegistrationCreateAPIView(
    CoreGenericPostAPIView,
    generics.GenericAPIView
):
    """
        POST Functionality for user registration form.
    """
    queryset = AccountsUserModel.objects.all()
    logger = logging.LoggerAdapter(
        admin_flow_logger, {"app_name": "AdminClientAdminRegistrationCreateAPIView"}
    )

    """ User Registraion API """
    def get_serializer_class(self):
        """
        Return the serializer class dynamicaly w.r.t to API method.
        """
        serializer_class = {
            "POST": AdminClientAdminRegistrationCreateSerializer,
        }
        return serializer_class.get(self.request.method)
    

class AdminAuthenticationVerifyOtpAPIView(generics.GenericAPIView):
    queryset = AccountsUserModel.objects.all()
    serializer_class = AdminAuthenticationVerifyOtpSerializer
    logger = logging.LoggerAdapter(
        admin_flow_logger, {"app_name": "AdminAuthenticationVerifyOtpAPIView"}
    )

    """ OTP Verification API """

    def post(self, request):
        try:
            serializer = self.serializer_class(
                data=request.data, context={"logger": self.logger}
            )
            if serializer.is_valid():
                serializer.save()
                self.logger.info("OTP Verified")
                return Response(
                    {"message": "OTP Verified successfully"}, status=status.HTTP_200_OK
                )
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.logger.info(f"Exception Verify OTP {str(e)}")
            return Response(
                {"message": EXCEPTION_MESSAGE},
                status=status.HTTP_400_BAD_REQUEST,
            )

from django.db.models.functions import ExtractYear
from django.db.models  import Q, F
class AdminClientDashBoardNoOfJobPostedByCompanyAPIView(
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
        admin_flow_logger, {"app_name": "AdminClientDashBoardNoOfJobPostedByCompanyAPIView"}
    )

    def get(self, request, *args, **kwargs):
        year = request.query_params.get('year')
        
        # Create base query for all companies
        employers = (
            AccountsUserModel.objects
            .filter(user_type="EMPLOYER")
            .select_related("company")
            .annotate(
                job_post_count=Count(
                    "company__EmployerJobDetailsModel_company",
                    filter=Q(company__EmployerJobDetailsModel_company__created_at__year=year) if year else Q(),
                    distinct=True
                ),
                title=F("company__title")
            )
            .values("id", "title", "job_post_count")
        )

        return Response({
            "data": list(employers),
            "year": year
        })

class AdminClientDashBoardActiveInactiveCompanyAPIView(
    CoreGenericCustomPaginationAPIView,
    generics.GenericAPIView
):
    """
        GET Functionality to get count active and inactive companies count.
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]

    success_message = SHORTLIST_JOB_SUCCESS_MESSAGE

    
    logger = logging.LoggerAdapter(
        admin_flow_logger, {"app_name": "AdminClientDashBoardActiveInactiveCompanyAPIView"}
    )

    def get(self, request, *args, **kwargs):
       
       active_company_count = AccountsUserModel.objects.filter(is_active = True,user_type = "EMPLOYER").count()
       inactive_company_count = AccountsUserModel.objects.filter(is_active = False,user_type = "EMPLOYER").count()

       return Response(
           {
            "active_company_count": active_company_count,
            "inactive_company_count": inactive_company_count
        }
    )

from django.db.models.functions import TruncMonth
import calendar

class AdminClientDashBoardApplicantsCountAPIView(
    CoreGenericCustomPaginationAPIView,
    generics.GenericAPIView
):
    """
        GET Functionality to get count of aplicant's by month.
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]

    success_message = SHORTLIST_JOB_SUCCESS_MESSAGE

    
    logger = logging.LoggerAdapter(
        admin_flow_logger, {"app_name": "AdminClientDashBoardApplicantsCountAPIView"}
    )

    def get(self, request, *args, **kwargs):
        requested_year = request.query_params.get('year')
        year_to_filter = int(requested_year) if requested_year else datetime.now().year
        
        self.logger.info(f"Filtering applicants for year: {year_to_filter}")

        applicants_per_month = (
            AccountsApplyJobHistoryModel.objects
            .filter(
                Q(created_at__year=year_to_filter)
            )
            .annotate(
                month=TruncMonth('created_at')
            )
            .values('month')
            .annotate(
                applicant_count=Count('id', distinct=True)
            )
            .order_by('month')
        )

        self.logger.info(f"Generated Query: {applicants_per_month.query}")

        applicant_data = {i: 0 for i in range(1, 13)}
        
        for entry in applicants_per_month:
            if entry["month"] and entry["month"].year == year_to_filter:
                applicant_data[entry["month"].month] = entry["applicant_count"]

        full_data = [
            {
                "month": calendar.month_name[i],
                "count": applicant_data[i]
            }
            for i in range(1, 13)
        ]

        self.logger.info(f"Response data prepared for year {year_to_filter}: {full_data}")

        return Response({
            "applicants_per_month": full_data,
            "year": year_to_filter,
            "total_applicants": sum(applicant_data.values())
        })
       


class AdminClientDashBoardManageClientsAPIView(
    CoreGenericCustomPaginationAPIView,
    generics.GenericAPIView
):
    """
        GET Functionality to get data of company & applicant's.
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]
    serializer_class = AdminDashboardManageClientsSerializer
    success_message = SHORTLIST_JOB_SUCCESS_MESSAGE

    logger = logging.LoggerAdapter(
        admin_flow_logger, {"app_name": "AdminClientDashBoardManageClientsAPIView"}
    )
    filter_backends = [
        filters.SearchFilter,
        django_filters.rest_framework.DjangoFilterBackend
    ]
    search_fields = [
        "company__title"
    ]
    
    
    def get_queryset(self):
        params = self.request.GET.dict()
        user = self.request.user 

        queryset = (
        AccountsUserModel.objects
        .filter(user_type='EMPLOYER')  # Filter for EMPLOYER users
        .select_related('company')  # Optimize company relation lookup
        .annotate(
            job_count=Count(
                'company__EmployerJobDetailsModel_company',  # Count jobs through company relation
                distinct=True
            ),
            applicant_count=Count(
                'company__AccountsApplyJobHistoryModel_company',  # Count applicants through company relation
                distinct=True
            )
        )
        .exclude(id=user.id)  # Exclude the logged-in user
        .order_by('-created_at')
    )

    # Apply search filter on the existing queryset
        search_term = params.get('search', '')
        if search_term:
            queryset = queryset.filter(
                Q(company__title__icontains=search_term)
            )
        return queryset

class AdminClientDashBoardManageApplicantsAPIView(
    CoreGenericCustomPaginationAPIView,
    generics.GenericAPIView
):
    """
        GET Functionality to get data of  applicants.
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]
    serializer_class = AdminDashboardManageApplicantsSerializer
    filter_backends = [
        filters.SearchFilter,
        django_filters.rest_framework.DjangoFilterBackend
    ]
    success_message = SHORTLIST_JOB_SUCCESS_MESSAGE

    search_fields = [
        "last_name",
        "username",
        "last_name"
    ]
    logger = logging.LoggerAdapter(
        admin_flow_logger, {"app_name": "AdminClientDashBoardManageApplicantsAPIView"}
    )
    def get_queryset(self):
        params = self.request.GET.dict()
        cv_subquery = AccountsUserResumeModel.objects.filter(
            candidate=OuterRef('id')
        ).values('cv')[:1]
        resume_exists_subquery = AccountsUserResumeModel.objects.filter(
                candidate=OuterRef('id')
            ).values('id')
        queryset = (
            AccountsUserModel.objects
            .filter(user_type='CANDIDATE')
            .annotate(
                jobs_applied_count=Count(
                    'AccountsApplyJobHistoryModel_candidate',
                    distinct=True
                ),
                cv=Subquery(cv_subquery),
                has_resume=Exists(resume_exists_subquery)
            ).filter(has_resume = True)
        )
        search_term = params.get('search', '')
        if search_term:
            queryset = queryset.filter(  # Use the existing queryset instead of creating new
                Q(first_name__icontains = search_term) |
                Q(last_name__icontains = search_term) |
                Q(username__icontains = search_term) 
            )
        return queryset

class AdminDashboardClientGETCandidateDetailsAPIView(
    CoreGenericGetAPIView,
    generics.GenericAPIView
):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]

    queryset = AccountsUserResumeModel.objects.all()

    logger = logging.LoggerAdapter(
        admin_flow_logger,{"app_name":"AdminDashboardClientGETCandidateDetailsAPIView"}
    )
    
    def get_queryset(self):
        """
        Returns a filtered queryset based on `candidate_id` and `job_id` from the request.
        """
        params = self.request.GET.dict()
        candidate_id = params.get("candidate_id")

        queryset = AccountsApplyJobHistoryModel.objects.filter(
            candidate__id=candidate_id
        ).select_related("candidate", "resume").order_by("-created_at")[:1]

        return queryset

    def get_serializer_class(self):
        """
        Returns the serializer class dynamically.
        """
        return AdminClientGETCandidateDetailsSerializer

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

class AdminClientManageClientAuthenticationUpdateAPIView(
    CoreGenericPutAPIView,
    CoreGenericDeleteAPIView,
    CoreGenericNonPaginatedFilterAPIView,
    generics.GenericAPIView
):
    """
       PUT Functionality for client Profile Management Page API.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    authentication_classes = [CustomAuthentication]
   
    logger = logging.LoggerAdapter(
        admin_flow_logger, {"app_name": "AdminClientManageClientAuthenticationUpdateAPIView"}
    )
    queryset = AccountsUserModel.objects.all()
    many= False

    success_message = USER_PROFILE_SUCCESS_MESSAGE

    def get_queryset(self):
        company_id = self.request.GET.get("company_id")
        if not company_id:
            return AccountsUserModel.objects.none()
        return AccountsUserModel.objects.filter(id=company_id)
    
    def get_serializer_class(self):
        """
        Return the serializer class dynamicaly w.r.t to API method.
        """
        serializer_class = {
            "PUT": AdminManageClientUserProfileUpdateSerializer,
            "DELETE": AdminClientDeleteCompanySerializer,
            "GET": AdminGetClientUserProfileInfoSerializer,
        }
        return serializer_class.get(self.request.method)
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset().first()  # Get single object instead of queryset
        if not queryset:
            return Response(
                {"message": "No data found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(queryset)  # Remove `many=True`
        
        return Response(
            {"result": serializer.data, "message": "Success"},
            status=status.HTTP_200_OK,
        )