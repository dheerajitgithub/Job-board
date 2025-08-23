"""urls for accounts app"""

from django.urls import path,include
# from accounts.generics.v1 import views

urlpatterns = [
    path(
        "api/authentication/v1/",include("accounts.authentication.v1.urls"),
    ),
    path(
        "api/generics/v1/",include("accounts.generics.v1.urls"),
    )
]
