import datetime
import logging
import jwt
import threading
from accounts.models import AccountsUserModel
from core.settings import SECRET_KEY, logger
from core.utils.emails import send_an_email
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from rest_framework import serializers
from typing import Union
from core.utils.contants import (
    INCORRECT_EMAIL,
)

logger = logging.LoggerAdapter(logger, {"app_name": "accounts.authentication.v1.utils.utils"})


def encode_jwt(user_id : str) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.now() + datetime.timedelta(days=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token.decode()

# Function to decode the JWT
def decode_jwt(token : str) -> Union[str, object]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return "Token has expired"
    except jwt.InvalidTokenError:
        return "Invalid token"

def forgot_password_send_email(email : str, ui_host : str)->None:
    """
        Args:
            email(str) -> Email address of the user.
            ui_host(str) -> The host URL for the UI.
        description:
            function for sending mail while forgot password 
        return:
            None 
    """
    try:
        user_instance = AccountsUserModel.objects.get(email=email)
    except AccountsUserModel.DoesNotExist:
        raise serializers.ValidationError(INCORRECT_EMAIL)

    token = encode_jwt(str(user_instance.id))
    context = {
        "username": user_instance.username,
        "ui_route": f"{ui_host}/auth/update-password?user_id={token}"
    }
    message = render_to_string("auth/forgot_password.html", context)
    
    thread = threading.Thread(
        target=send_an_email,
        kwargs={
            "receiver_email": [email],
            "subject": "JobBoard | Forgot password",
            "body": message
        }
    )
    thread.start()
