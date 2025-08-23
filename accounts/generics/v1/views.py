"""Generics APIViews for accounts"""

import logging
from rest_framework.views import APIView
from accounts.utils.country_code import country_codes
from core.utils.mixins import ResponseMixin
from core.settings import logger
from accounts.models import CountryMobileCodesModel


class AccountsGenericGetCountryCodesAPIView(APIView, ResponseMixin):
    """
    API for getting list of Country codes
    """
    api_logger = logging.LoggerAdapter(
        logger, {"app_name": "AccountsGenericGetCountryCodesAPIView"}
    )
   
    def get(self, request):
        """Get Country codes""" 
        try:
            queryset_vals = CountryMobileCodesModel.objects.all().distinct("currency").values(
                "country_name", "currency", "id")
            country_data = []
            for country in queryset_vals:
                if country.get("currency") != '':
                    country_data.append(country)
                else:
                    continue
            return self.success_response(msg = country_data)

        except Exception as e:
            self.api_logger.info(f"Get country codes API GET, {str(e)}")
            return self.error_response(data=str(e))


class AccountsGenericGetPhoneCodesAPIView(APIView, ResponseMixin):
    """
    API for getting list of Country codes
    """
    api_logger = logging.LoggerAdapter(
        logger, {"app_name": "AccountsGenericGetPhoneCodesAPIView"}
    )
    def get(self, request):
        """Get Country codes""" 
        try:
            values = country_codes
            final_values = []
            for value in values:
                if value not in final_values:
                    final_values.append(value)
            return self.success_response(msg = final_values)

        except Exception as e:
            self.api_logger.info(f"Get phone codes API GET, {str(e)}")
            return self.error_response(data=str(e))