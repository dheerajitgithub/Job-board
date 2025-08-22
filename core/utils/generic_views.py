"""Generic views for complete application"""

from rest_framework.response import Response
from rest_framework import status

from core.utils.contants import DEFAULT_API_SUCCESS_MESSAGES, EXCEPTION_MESSAGE
from core.utils.paginators import get_paginated_data
from .utils import extract_serializer_error
from core.settings import logger



class CoreGenericSucessMessageMethod:
    """
        Generic class for handling success message
    """
    success_message = DEFAULT_API_SUCCESS_MESSAGES

    def get_success_message(self):
        return self.success_message.get(self.request.method)


class CoreGenericAPIView(CoreGenericSucessMessageMethod):
    """
        Generic APIView for all the view APIs
    """
    def process_request(self, request):
        """
        function for  validating & saving request 
        """
        json_data = request.data
        if type(json_data) != dict:
            json_data = json_data.dict()
        serializer = self.get_serializer(
            data={
                **json_data,
                **request.GET.dict()
            }, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            data = serializer.data
            if not "custom_data" in data:
                return Response({
                    "results": (data
                            if data.get("data") is None
                            else dict(data)["data"]),
                    "message": data.get("success_msg", self.get_success_message())
                }, status=status.HTTP_200_OK)
            else:
                return Response(data["custom_data"], status=status.HTTP_200_OK)
        else:
            error = extract_serializer_error(serializer=serializer)
            return Response(
                {"message": error, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

    def custom_handle_exception(self, request, e):
        """
            Args:
                request -> The HTTP request object containing the data to be processed.
                e -> The exception object containing details about the error.
            description:
                Custom handler for exceptions that occur during API request processing.
            return:
                None 
        """
        self.logger.info(
            f"{type(self).__name__} Method {request.method} API Exception, {str(e)}")
        return Response(
            {"message": self.get_error_msg(e), "error": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def get_error_msg(self, e):
        print(1, e)
        try:
            if "integrity_error" in str(e.get_full_details()):
                print(2)
                error_msg = e.get_full_details()["integrity_error"]["message"]
            else:
                print(4)
                error_msg = EXCEPTION_MESSAGE
        except:
            print(99, e)
            error_msg = EXCEPTION_MESSAGE
        return error_msg

class CoreGenericListCreateAPIView(

    CoreGenericAPIView,
    CoreGenericSucessMessageMethod
):
    """
        Inherit this class to override get/list methods
        use get method for non paginate response
        use list method for paginate response
    """

    def list(self, request):
        """
            Args:
                request -> The HTTP request object containing the data to be processed.
            description:
                Retrieves a list of resources 
                from the queryset and returns 
                it in a serialized format.
            return:
                None 
        """
        try:
            serializer = self.get_serializer(
                self.paginate_queryset(
                    self.filter_queryset(self.get_queryset())),
                many=True,
                context={
                    "request": request
                }
            )
            return self.get_paginated_response(
                    serializer.data
            )
        except Exception as e:
            self.logger.info(
                f"{super().__class__} Method {request.method} API Exception, {str(e)}")
            return Response(
                {"message": EXCEPTION_MESSAGE, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def create(self, request):
        try:
            return self.process_request(request)
        except Exception as e:
            return self.custom_handle_exception(request, e)



class CoreGenericGETNonPaginateAPIView:
    """
        A generic API view for retrieving a list of resources and returning them in a serialized format 
        without pagination.
    """
    def get(self, request):
        """
            Args:
                request -> The HTTP request object containing the data to be processed.
            description:
               Retrieves a resource data present in the database.
            return:
                None 
        """
        try:
            serializer = self.get_serializer(
                self.get_queryset(),
                many=True,
                context={
                    "request": request,
                    "params": request.GET.dict()
                })
            return Response({
                "results": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            self.logger.info(
                f"{super().__class__} Method {request.method} API Exception, {str(e)}")
            return Response(
                {"message": EXCEPTION_MESSAGE, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CoreGenericPaginatedAPIView:
    """
        A generic API view for retrieving a list of resources and returning them in a serialized format 
        with django based pagination.
    """
    def get(self, request):
        try:
            serializer = self.get_serializer(
                self.paginate_queryset(
                    self.filter_queryset(self.get_queryset())),
                many=True,
                context={
                    "request": request
                }
            )
            return self.get_paginated_response(serializer.data)
        except Exception as e:
            self.logger.info(
                f"{super().__class__} Method {request.method} API Exception, {str(e)}")
            return Response(
                {"message": EXCEPTION_MESSAGE, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CoreGenericNonPaginatedFilterAPIView:
    """
        A generic API view for GET which is not Pagination and supports Filterset 
    """
    many = True
    def get(self, request):
        try:
            serializer = self.get_serializer(
                    self.filter_queryset(self.get_queryset()),
                many=self.many,
                context={
                    "request": request
                }
            )
            return Response({'results' : serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            self.logger.info(
                f"{super().__class__} Method {request.method} API Exception, {str(e)}")
            return Response(
                {"message": EXCEPTION_MESSAGE, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

class CoreGenericCustomPaginationAPIView:
    """
        A generic API view for retrieving a list of resources and returning them in a serialized format 
        with custom pagination.
    """
    def get(self, request):
        try:
            page = request.GET.dict().get("page", 1)
            serializer = self.get_serializer(
               self.filter_queryset( self.get_queryset()), many = True
            )
            final_data = get_paginated_data(
                request = request,
                queryset = serializer.data,
                page = page
            )
            return Response(final_data, status=status.HTTP_200_OK)
        except Exception as e:
            self.logger.info(
                f"{super().__class__} Method {request.method} API Exception, {str(e)}")
            return Response(
                {"message": EXCEPTION_MESSAGE, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CoreGenericCustomPaginationPerPageAPIView:
    """
        A generic API view for retrieving a list of resources and returning them in a serialized format 
        with custom pagination.
    """
    def get(self, request):
        try:
            page = request.GET.dict().get("page", 1)
            per_page = int(request.GET.dict().get("per_page", 30))
            serializer = self.get_serializer(
               self.filter_queryset( self.get_queryset()), many = True
            )
            final_data = get_paginated_data(
                request = request,
                queryset = serializer.data,
                page = page,
                per_page=per_page
            )
            return Response(final_data, status=status.HTTP_200_OK)
        except Exception as e:
            self.logger.info(
                f"{super().__class__} Method {request.method} API Exception, {str(e)}")
            return Response(
                {"message": EXCEPTION_MESSAGE, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CoreGenericGETModelSerializerNonPaginateAPIView:
    """
        A generic API view for retrieving data and returning it in a serialized format 
        without pagination.
    """
    def get(self, request):
        """
            Args:
                request -> The HTTP request object containing the data to be processed.
            description:
               Retrieves a resource data present in the database.
            return:
                None 
        """
        try:
            serializer = self.get_serializer(
                self.queryset.all(), many=True, context={"params": request.GET.dict(), 'request': request}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"message": EXCEPTION_MESSAGE, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CoreGenericGetAPIView(CoreGenericAPIView):
    def get(self, request):
        try:
            return self.process_request(request)
        except Exception as e:
            return self.custom_handle_exception(request, e)
class CoreGenericGetFromSerializerAPIView(CoreGenericAPIView):
    def get(self, request):
        try:
            serializer = self.get_serializer(
                data={
                    **request.data,
                    **request.GET.dict()
                }, context={
                    "request": request
                }
            )
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "results": serializer.data['data'],
                }, status=status.HTTP_200_OK)
            else:
                error = extract_serializer_error(serializer=serializer)
                return Response(
                    {"message": error, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return self.custom_handle_exception(request, e)

class CoreGenericPostAPIView(CoreGenericAPIView):
    """
        A generic API view for creating data 
        send by the user and returning it 
        in a serialized format.
    """
    def post(self, request):
        """
            Args:
                request -> The HTTP request object containing the data to be processed.
            description:
               Updates a resource data based on the given primary key(pk).
            return:
                None 
        """
        try:
            return self.process_request(request)
        except Exception as e:
            print(e)
            return self.custom_handle_exception(request, e)



class CoreGenericPutAPIView(CoreGenericAPIView):
    """
        A generic API view for Updating data and returning it in a serialized format.
    """
    def put(self, request):
        """
            Args:
                request -> The HTTP request object containing the data to be processed.
            description:
               Updates a resource data given by the user.
            return:
                None 
        """
        try:
            return self.process_request(request)
        except Exception as e:
            return self.custom_handle_exception(request, e)


class CoreGenericUpdateDetailsGenericGenericModelAPIView(CoreGenericSucessMessageMethod):
    """
        Basic Update Details with id for Model Serializer id from payload
    """
    lookup_field = "pk"
    # def get_object(self, )
    def put(self, request):
        """
            Args:
                request -> The HTTP request object containing the data to be processed.
                
            description:
               
            return:
                None
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, data={
                    **request.data,
                    **request.GET.dict()
                }, context={
                    "request": request, "pk": self.lookup_field}
            )
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "results": serializer.data,
                    "message": self.get_success_message()
                }, status=status.HTTP_200_OK)
            else:
                error = extract_serializer_error(serializer=serializer)
                return Response(
                    {"message": error, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            self.logger.info(
                f"{super().__class__} Method {request.method} API Exception, {str(e)}")
            return Response(
                {"message": EXCEPTION_MESSAGE, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CoreGenericPutWithPkAPIView(CoreGenericSucessMessageMethod):
    """
        A generic API view for Updating data  
        based on the given primary key (pk)
        and returning it in a serialized format.
    """
    def put(self, request, pk):
        """
            Args:
                request -> The HTTP request object containing the data to be processed.
            description:
               Updates a resource data based on the given primary key(pk).
            return:
                None 
        """
        try:
            serializer = self.get_serializer(
                data={
                    "pk": pk,
                    **request.data,
                    **request.GET.dict()
                }, context={
                    "request": request,
                    "pk": pk
                }
            )
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "results": serializer.data,
                    "message": self.get_success_message()
                }, status=status.HTTP_200_OK)
            else:
                error = extract_serializer_error(serializer=serializer)
                return Response(
                    {"message": error, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            self.logger.info(
                f"{super().__class__} Method {request.method} API Exception, {str(e)}")
            return Response(
                {"message": EXCEPTION_MESSAGE, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CoreGenericDeleteAPIView(CoreGenericAPIView):
    """
        A generic API view for Deleting data and returning it in a serialized format.
    """
    success_message = DEFAULT_API_SUCCESS_MESSAGES

    def get_success_message(self):
        return self.success_message.get(self.request.method)

    def delete(self, request):
        """
            Args:
                request -> The HTTP request object containing the data to be processed.
            description:
               Retrieves a resource based on the provided primary key (pk).
            return:
                None 
        """
        try:
            return self.process_request(request)
        except Exception as e:
            return self.custom_handle_exception(request, e)


class CoreGenericCreateWithOutErrorIteratorAPIView(
        CoreGenericAPIView,
        CoreGenericSucessMessageMethod):
    """CoreGenericCreateWithOutErrorIteratorAPIView"""

    def create(self, request):
        """
            Args:
                request -> The HTTP request object containing the data to be processed.
            description:
                Handles the creation of a new resource based on the provided request.
            return:
                None 
        """
        try:
            return self.process_request(request)
        except Exception as e:
            return self.custom_handle_exception(request, e)


class CoreGenericGetDetailsGenericAPIView:
    """
        Basic GET Details with id for Model Serializer
    """
    INCORRECT_ID_EXCEPTION = "'Incorrect Id'"

    def get(self, request):
        """
            Args:
                request -> The HTTP request object containing the data to be processed.
                Pk -> Retrieves a resource based on the provided primary key (pk).
            description:
               Retrieves a resource data present in the database.
            return:
                None
        """
        try:
            pk = request.GET.dict().get("id")
            if not self.queryset.filter(pk=pk).exists():
                return Response({
                    "message": self.INCORRECT_ID_EXCEPTION
                },
                    status=status.HTTP_400_BAD_REQUEST)
            serializer = self.get_serializer(
                self.queryset.get(pk=pk),
                many=False,
                context={
                    "request": request,
                    "pk": pk
                }
            )
            return Response({'results': serializer.data})
        except Exception as e:
            self.logger.info(
                f"{super().__class__} Method {request.method} API Exception, {str(e)}")
            return Response(
                {"message": EXCEPTION_MESSAGE, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )




class CoreGenericUpdateDetailsGenericGenericModelAPIView(CoreGenericSucessMessageMethod):
    """
        Basic Update Details with id for Model Serializer id from payload
    """
    lookup_field = "pk"
    # def get_object(self, )
    def put(self, request):
        """
            Args:
                request -> The HTTP request object containing the data to be processed.
                
            description:
               
            return:
                None 
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, data={
                    **request.data,
                    **request.GET.dict()
                }, context={
                    "request": request, "pk": self.lookup_field}
            )
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "results": serializer.data,
                    "message": self.get_success_message()
                }, status=status.HTTP_200_OK)
            else:
                error = extract_serializer_error(serializer=serializer)
                return Response(
                    {"message": error, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            self.logger.info(
                f"{super().__class__} Method {request.method} API Exception, {str(e)}")
            return Response(
                {"message": EXCEPTION_MESSAGE, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

class CoreGenericUpdateDetailsGenericAPIView(CoreGenericSucessMessageMethod):
    """
        Basic Update Details with id for Model Serializer
    """

    def put(self, request, pk):
        """
            Args:
                request -> The HTTP request object containing the data to be processed.
                Pk -> Retrieves a resource based on the provided primary key (pk).
            description:
               Updates a resource based on the provided primary key (pk) by the user.
            return:
                None 
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, data={
                    **request.data,
                    **request.GET.dict()
                }, context={
                    "request": request, "pk": pk}
            )
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "results": serializer.data,
                    "message": self.get_success_message()
                }, status=status.HTTP_200_OK)
            else:
                error = extract_serializer_error(serializer=serializer)
                return Response(
                    {"message": error, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            self.logger.info(
                f"{super().__class__} Method {request.method} API Exception, {str(e)}")
            return Response(
                {"message": EXCEPTION_MESSAGE, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

