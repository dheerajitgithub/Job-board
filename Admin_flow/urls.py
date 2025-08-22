"""urls for candidate.app"""

from django.urls import path,include


urlpatterns = [
    path(
        "api/admin-dashboard/v1/",
        include("Admin_flow.client.urls")
    )
]