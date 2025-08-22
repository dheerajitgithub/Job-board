from rest_framework import serializers
from django.db import IntegrityError
from core.utils.contants import DEAFULT_INCORRECT_ID_ERROR_MESSAGE
from core.utils.utils import is_filter_required


# class CoreGenericUpdateTitleUniqueDirectInstanceSerializer:
#     """
#         This serializer should be used if all values in model
#         updated directly and if title is unique
#     """

#     def validate(self, data):
#         if not self.queryset.filter(pk=data['id']).exists():
#             raise serializers.ValidationError(self.INCORRECT_ID_ERROR_MESSAGE)
#         master_tag_instance = self.queryset.get(pk=data['id'])
#         if master_tag_instance.title != data['title'] and self.queryset.filter(title=data['title']).exists():
#             raise serializers.ValidationError(self.TITLE_ALREADY_ERROR_MESSAGE)
#         return data

#     def create(self, validated_data):
#         pk = validated_data['id']
#         self.queryset.filter(pk=pk).update(**validated_data)
#         return validated_data


class CoreGenericTitleValidatorSerializer:
    """
        This validate function validates titles if it is unique
        and raises custom error message
    """
    TITLE_ALREADY_ERROR_MESSAGE = "Value already exists"

    def validate(self, data):
        if self.queryset.filter(**data).exists():
            raise serializers.ValidationError(
                self.TITLE_ALREADY_ERROR_MESSAGE)
        return data


class CoreGenericIdValidatorSerializer:
    """
        This validate function validates id 
    """
    INCORRECT_ID_ERROR_MESSAGE = DEAFULT_INCORRECT_ID_ERROR_MESSAGE

    def validate(self, data):
        if not self.queryset.filter(pk=data['id']).exists():
            raise serializers.ValidationError(
                self.INCORRECT_ID_ERROR_MESSAGE)
        return data


class CoreGenericParamIdValidatorSerializer:
    """
        This validate function validates id from params
    """
    INCORRECT_ID_ERROR_MESSAGE = DEAFULT_INCORRECT_ID_ERROR_MESSAGE

    def validate(self, data):
        params = self.context["request"].GET.dict()
        if not self.queryset.filter(pk=params['id']).exists():
            raise serializers.ValidationError(
                self.INCORRECT_ID_ERROR_MESSAGE)
        return data

class CoreGenericIdTitleValidatorSerializer:
    """
        This validate function validates id and title
    """
    INCORRECT_ID_ERROR_MESSAGE = DEAFULT_INCORRECT_ID_ERROR_MESSAGE
    TITLE_ALREADY_ERROR_MESSAGE = "Value already exists"

    def validate(self, data):
        if not self.queryset.filter(pk=data['id']).exists():
            raise serializers.ValidationError(
                self.INCORRECT_ID_ERROR_MESSAGE)
        filter_data = data.copy()
        pk = filter_data.pop("id")
        if not is_filter_required("is_active",data) and  self.queryset.filter(**filter_data).exclude(id=pk).exists():
            raise serializers.ValidationError(
                self.TITLE_ALREADY_ERROR_MESSAGE)
        return data


class CoreGenericMultipleObjectDeleteSerializer:
    INCORRECT_DELETE_ID_ERROR_MESSAGE = "Incorrect Delete id"

    def validate(self, data):
        if self.queryset.filter(id__in=data['delete_id']).count() != len(data['delete_id']):
            raise serializers.ValidationError(
                self.INCORRECT_DELETE_ID_ERROR_MESSAGE)
        return data

    def create(self, validated_data):
        self.queryset.filter(
            id__in=validated_data['delete_id']).delete()
        return validated_data


class CoreGenericSingleObjectDeleteSerializer:
    INCORRECT_DELETE_ID_ERROR_MESSAGE = "Incorrect Delete id"

    def validate(self, data):
        if not self.queryset.filter(id=data['id']).exists():
            raise serializers.ValidationError(
                self.INCORRECT_DELETE_ID_ERROR_MESSAGE)
        return data

    def create(self, validated_data):
        self.queryset.filter(
            id=validated_data['id']).delete()
        return validated_data


class CoreGenericsCreateGenericObjectSerializer:

    TITLE_ALREADY_ERROR_MESSAGE = "Value already exists"

    def create(self, validated_data):
        try:
            self.queryset.create(**validated_data)
        except IntegrityError:
            raise serializers.ValidationError({"integrity_error" : self.TITLE_ALREADY_ERROR_MESSAGE})
        return validated_data


class CoreGenericsUpdateGenericObjectSerializer:
    INCORRECT_ID_ERROR_MESSAGE = DEAFULT_INCORRECT_ID_ERROR_MESSAGE

    def validate(self, data):
        if not self.queryset.filter(pk=data['id']).exists():
            raise serializers.ValidationError(
                self.INCORRECT_ID_ERROR_MESSAGE)
        return data

    def create(self, validated_data):
        pk = validated_data.pop("id")
        self.queryset.filter(pk=pk).update(**validated_data)
        validated_data['id'] = pk
        return validated_data


class CoreGenericsUpdateGenericObjectValidateNameSerializer:
    INCORRECT_ID_ERROR_MESSAGE = DEAFULT_INCORRECT_ID_ERROR_MESSAGE
    TITLE_ALREADY_ERROR_MESSAGE = "Value already exists"

    def validate(self, data):
        if not self.queryset.filter(pk=data['id']).exists():
            raise serializers.ValidationError(
                self.INCORRECT_ID_ERROR_MESSAGE)
        return data

    def create(self, validated_data):
        print("in create")

        pk = validated_data.pop("id")
        try:
            self.queryset.filter(pk=pk).update(**validated_data)
        except IntegrityError:
            raise serializers.ValidationError({"integrity_error" : self.TITLE_ALREADY_ERROR_MESSAGE})
        
        validated_data['id'] = pk
        return validated_data
