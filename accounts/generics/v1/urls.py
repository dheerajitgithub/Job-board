"""urls for accounts.generic"""

from django.urls import path,include
from accounts.generics.v1 import views as accounts_generic_views


urlpatterns = [
    path(
        "country-codes-api/",
        accounts_generic_views.AccountsGenericGetCountryCodesAPIView.as_view(),
        name="AccountsGenericGetCountryCodesAPIView"
    ),
    path(
        "phone-codes-api/",
        accounts_generic_views.AccountsGenericGetPhoneCodesAPIView.as_view(),
        name="AccountsGenericGetPhoneCodesAPIView"
    )
]
