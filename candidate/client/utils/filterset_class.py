


import json
from datetime import datetime, timedelta
import django_filters
from rest_framework.response import Response
from employer.models import EmployerJobDetailsModel
from rest_framework.pagination import PageNumberPagination


class DynamicPageSizePagination(PageNumberPagination):
    # Remove page_size_query_param = 'page' since we want to handle it directly
    max_page_size = 100
    
    def paginate_queryset(self, queryset, request, view=None):
        # Get the page size from the 'page' parameter
        try:
            requested_page_size = int(request.query_params.get('page', self.page_size))
            self.page_size = min(requested_page_size, self.max_page_size)
        except (TypeError, ValueError):
            self.page_size = 10  # default if invalid value
            
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'results': data
        })

class CandidateJobsDashboardModelFilterSet(django_filters.FilterSet):
    job_type = django_filters.CharFilter(method="filter_job_type")
    created_at = django_filters.CharFilter(method="filter_by_time_range")
    location = django_filters.CharFilter(method="filter_by_location")
    order_by = django_filters.CharFilter(method="filter_order_by")

    class Meta:
        model = EmployerJobDetailsModel
        fields = [
            "job_type",
            "created_at",
            "location",
            "order_by"
        ]
    def filter_job_type(self, queryset, name, value):
        job_type_mapping = {
            "FULL_TIME": "FULL_TIME",
            "CONTRACT": "CONTRACT",
            "INTERNSHIP": "INTERNSHIP",
        }
        selected_job_types = value.split(',')
        actual_values = [job_type_mapping.get(job_type) for job_type in selected_job_types if job_type in job_type_mapping]
        
        if actual_values:
            return queryset.filter(job_type__in=actual_values)
        return queryset 
    
    def filter_by_time_range(self, queryset, name, value):
        if value == "Today":
            return queryset.filter(created_at__date=datetime.today().date())
        elif value == 'past_hour':
            return queryset.filter(created_at__gte=datetime.now() - timedelta(hours=1))
        elif value == 'past_24_hours':
            return queryset.filter(created_at__gte=datetime.now() - timedelta(days=1))
        elif value == 'past_14_days':
            return queryset.filter(created_at__gte=datetime.now() - timedelta(days=14))
        elif value == 'past_week':
            return queryset.filter(created_at__gte=datetime.now() - timedelta(weeks=1))
        elif value == 'past_month':
            return queryset.filter(created_at__gte=datetime.now() - timedelta(days=30))
        return queryset
    

    def filter_by_location(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(location__icontains=value)
    
    def filter_order_by(self, queryset, name, value):
        if value == "order_by_recent":
            return queryset.order_by("-created_at")
        elif value == "order_by_oldest":
            return queryset.order_by("created_at")
        return queryset