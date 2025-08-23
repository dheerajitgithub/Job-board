"""urls for accounts.auth.app"""

from django.urls  import path
from rest_framework_jwt.views import ObtainJSONWebTokenView
from accounts.authentication.v1.serializers import CustomJWTSerializer
from accounts.authentication.v1 import views as authentication_views


urlpatterns = [
    path(
        "user-login-api/",
        ObtainJSONWebTokenView.as_view(serializer_class = CustomJWTSerializer),
        name="LoginAPIView"
    ),
    path(
        "user-registration-api/",
        authentication_views.AccountsAuthenticationUsersRegistrationCreateAPIView.as_view(),
        name="AccountsAuthenticationUsersRegistrationCreateAPIView",
    ),
    path(
        "verify-otp-api/",
        authentication_views.AccountsAuthenticationVerifyOtpAPIView.as_view(),
        name="AccountsAuthenticationVerifyOtpAPIView",
    ),
    path(
        "resend-otp-api/",
        authentication_views.AccountsAuthenticationResendOtpAPIView.as_view(),
        name="AccountsAuthenticationResendOtpAPIView",
    ),
    path(
        "forgot-password-api/",
        authentication_views.AccountsAuthForgotPasswordAPIView.as_view(),
        name="AccountsAuthForgotPasswordAPIView",
    ),
    path(
        "change-password-api/",
        authentication_views.AccountsAuthChangePasswordAPIView.as_view(),
        name="ProfilesAuthChangePasswordAPIView",
    ),
    path(
        "logout-api/",
        authentication_views.AccountsAuthLogoutAPIView.as_view(),
        name="AccountsAuthLogoutAPIView",
    ),
    path(
        "profile-management-api/",
        authentication_views.AccountsAuthenticationUserProfileUpdateAPIView.as_view(),
        name="AccountsAuthenticationUserProfileUpdateAPIView",
    ),
    path(
        "currency-list-api/",
        authentication_views.AccountsAuthenticationCurrenciesListAPIView.as_view(),
        name="AccountsAuthenticationCurrenciesListAPIView",
    ),
    path(
        "cities-api/",
        authentication_views.AccountsAuthenticationGetCitiesAPIView.as_view(),
        name="AccountsAuthenticationGetCitiesAPIView",
    ),
]