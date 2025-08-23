"""urls for candidate.app"""

from django.urls import path,include


urlpatterns = [
    path(
        "api/manage-candidate/v1/",
        include("candidate.client.urls")
    )
]