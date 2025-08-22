"""Views for accounts.authentication"""

import logging
# from flask import Response
from rest_framework import generics,status,response,views
from rest_framework.response import Response
from operator import itemgetter
from rest_framework import permissions
from accounts.models import AccountsUserModel
from accounts.utils import  countries
from accounts.utils.cities import cities
from core.utils.authentications import CustomAuthentication 
from core.utils.generic_views import ( 
    CoreGenericGetAPIView,
    CoreGenericNonPaginatedFilterAPIView,
    CoreGenericPostAPIView,
    CoreGenericPutAPIView,
    CoreGenericUpdateDetailsGenericGenericModelAPIView
)
from core.settings import logger as user_mgt_logger
from core.utils.contants import (
    DEFAULT_API_SUCCESS_MESSAGES,
    EXCEPTION_MESSAGE,
    LOGOUT_SUCESSFULLY_MESSAGE,
    PASSWORD_CHANGE_SUCESSFULLY_MESSAGE,
    USER_PROFILE_SUCCESS_MESSAGE,
)
from core.settings import logger
from accounts.authentication.v1.serializers import (
    AccountsAuthForgotPasswordSerializer,
    AccountsAuthForgotPasswordUpdateSerializer,
    AccountsAuthLogoutSerializer,
    AccountsAuthChangePasswordSerializer,
    AccountsAuthenticationGetUserProfileInfoSerializer,
    AccountsAuthenticationResendOtpSerializer,
    AccountsAuthenticationUserProfileUpdateSerializer,
    AccountsAuthenticationUsersRegistrationCreateSerializer,
    AccountsAuthenticationVerifyOtpSerializer,
    # AccountsUpdateUsersProfile,
)


class AccountsAuthForgotPasswordAPIView(
    CoreGenericPostAPIView,
    CoreGenericPutAPIView,
    generics.GenericAPIView
):
    """
       POST, PUT Functionality for Change Password in Forgot Password Page API
    """
    success_message = PASSWORD_CHANGE_SUCESSFULLY_MESSAGE
    logger = logging.LoggerAdapter(
        user_mgt_logger, {"app_name": "AccountsAuthForgotPasswordAPIView"}
    )

    def get_serializer_class(self):
        """
        Return the serializer class dynamicaly w.r.t to API method.
        """
        serializer_class = {
            "POST": AccountsAuthForgotPasswordSerializer,
            "PUT" : AccountsAuthForgotPasswordUpdateSerializer
        }
        return serializer_class.get(self.request.method)


class AccountsAuthLogoutAPIView(
    CoreGenericPostAPIView,
    generics.GenericAPIView
):
    """
       POST Functionality for Logout Page API
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]
    logger = logging.LoggerAdapter(
        user_mgt_logger, {"app_name": "AccountsAuthLogoutAPIView"}
    )
    success_message = LOGOUT_SUCESSFULLY_MESSAGE

    def get_serializer_class(self):
        """
        Return the serializer class dynamicaly w.r.t to API method.
        """
        serializer_class = {
            "POST": AccountsAuthLogoutSerializer,
        }
        return serializer_class.get(self.request.method)


class AccountsAuthChangePasswordAPIView(
    CoreGenericPutAPIView,
    generics.GenericAPIView
):
    """
       PUT Functionality for Change Password Page API
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]
    logger = logging.LoggerAdapter(
        user_mgt_logger, {"app_name": "AccountsAuthChangePasswordAPIView"}
    )

    def get_serializer_class(self):
        """
        Return the serializer class dynamicaly w.r.t to API method.
        """
        serializer_class = {
            "PUT": AccountsAuthChangePasswordSerializer,
        }
        return serializer_class.get(self.request.method)
    
    

class AccountsAuthProfileManagementAPIView(
    CoreGenericPutAPIView,
    generics.GenericAPIView
):
    """
       PUT Functionality for Profile Management Page API
    """
    logger = logging.LoggerAdapter(
        user_mgt_logger, {"app_name": "AccountsAuthProfileManagementAPIView"}
    )

    def get_serializer_class(self):
        """
        Return the serializer class dynamicaly w.r.t to API method.
        """
        serializer_class = {
            "PUT": AccountsAuthChangePasswordSerializer,
        }
        return serializer_class.get(self.request.method)


from rest_framework.generics import get_object_or_404

class AccountsAuthenticationUsersRegistrationCreateAPIView(
    CoreGenericPostAPIView,
    generics.GenericAPIView
):
    """
        POST Functionality for user registration form.
    """
    queryset = AccountsUserModel.objects.all()
    logger = logging.LoggerAdapter(
        user_mgt_logger, {"app_name": "AccountsAuthenticationUsersRegistrationCreateAPIView"}
    )
    """ User Registraion API """
    def get_serializer_class(self):

        """
        Return the serializer class dynamicaly w.r.t to API method.
        """
        serializer_class = {
            "POST": AccountsAuthenticationUsersRegistrationCreateSerializer,
        }
        return serializer_class.get(self.request.method)
    
class AccountsAuthenticationVerifyOtpAPIView(generics.GenericAPIView):
    queryset = AccountsUserModel.objects.all()
    serializer_class = AccountsAuthenticationVerifyOtpSerializer
    logger = logging.LoggerAdapter(
        user_mgt_logger, {"app_name": "ClientAccountsVerifyOtpAPIView"}
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
        

class AccountsAuthenticationResendOtpAPIView(generics.GenericAPIView):
    queryset = AccountsUserModel.objects.all()
    serializer_class = AccountsAuthenticationResendOtpSerializer

    logger = logging.LoggerAdapter(
        user_mgt_logger, {"app_name": "AccountsAuthenticationResendOtpAPIView"}
    )

    """ Resend OTP for both register and forgot password """

    def post(self, request):
        try:
            serializer = self.serializer_class(
                data=request.data, context={"logger": self.logger}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"message": "OTP sent successfully"}, status=status.HTTP_200_OK
                )
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.logger.info(f"Exception Resend OTP, {str(e)}")
            return Response(
                {"message": EXCEPTION_MESSAGE},
                status=status.HTTP_400_BAD_REQUEST,
            )


class AccountsAuthenticationUserProfileUpdateAPIView(
    CoreGenericPutAPIView,
    CoreGenericNonPaginatedFilterAPIView,
    generics.GenericAPIView
):
    """
       PUT Functionality for Profile Management Page API
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]
   
    logger = logging.LoggerAdapter(
        logger, {"app_name": "AccountsAuthenticationUserProfileUpdateAPIView"}
    )
    queryset = AccountsUserModel.objects.all()
    many= False

    success_message = USER_PROFILE_SUCCESS_MESSAGE

    def get_object(self):
        """
        Returns the object the view is displaying.

        You may want to override this if you need to provide non-standard
        queryset lookups.  Eg if objects are referenced using multiple
        keyword arguments in the url conf.
        """
        queryset = self.filter_queryset(self.queryset.all())

        filter_kwargs = {self.lookup_field: self.request.user.pk}
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        return obj
    
    def get_queryset(self):
        return self.get_object()
    
    def get_serializer_class(self):
        """
        Return the serializer class dynamicaly w.r.t to API method.
        """
        serializer_class = {
            "PUT": AccountsAuthenticationUserProfileUpdateSerializer,
            "GET": AccountsAuthenticationGetUserProfileInfoSerializer
        }
        return serializer_class.get(self.request.method)


class AccountsAuthenticationCurrenciesListAPIView(views.APIView):

    """this method will return the currencies of all the countries"""
    logger = logging.LoggerAdapter(
        logger, {"app_name": "AccountsAuthenticationCurrenciesListAPIView"}
    )

    def get(self, request):
        try:
            res = sorted(set(map(itemgetter("Currency"), countries.country_codes)))
            res = [e for e in res if e != ""]
            return Response({"message": res}, status=status.HTTP_200_OK)
        except Exception as e:
            self.logger.info(f"Currencies API Exception, {str(e)}")
            return Response(
                {"message": EXCEPTION_MESSAGE},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
class AccountsAuthenticationGetCitiesAPIView(views.APIView):


    logger = logging.LoggerAdapter(
        logger, {"app_name": "AccountsAuthenticationGetCitiesAPIView"}
    )

    def get(self, request):
        try:
            self.logger.info(f"No. of cities generated : {len(cities)}")
            return Response(
                {"data":cities,"message": "Success"}, status=status.HTTP_200_OK
            )
        except Exception as e:
            self.logger.info(f"Cities API Exception, {str(e)}")
            return Response(
                {"message": EXCEPTION_MESSAGE},
                status=status.HTTP_400_BAD_REQUEST,
            )