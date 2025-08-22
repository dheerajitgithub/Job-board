"""main url file for employer.clients"""

from django.urls import path,include


urlpatterns = [
    path("api/manage-job/v1/",include("employer.client.urls")),
]