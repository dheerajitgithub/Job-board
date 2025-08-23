"""filets classes for employer.serializer's"""

import django_filters
from employer.models import EmployerJobDetailsModel


class EmployerManageJobsModelFilterSet(django_filters.FilterSet):
    def filter_tasks(self, queryset, name, value):
        return queryset.filter(tasks__id__in=value.split(','))
    class Meta:
        model = EmployerJobDetailsModel
        fields = [
            "location"
        ]