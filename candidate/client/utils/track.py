import datetime

import pytz
from accounts.models import AccountsUserModel
from core.utils.utils import get_details_from_request
from employer.models import CompanyDetailModel, EmployerJobDetailsModel, EmployerTrackerModel


def is_already_tracking_date_saved(request):
    """Check if tracking data is already saved in PostgreSQL"""
    
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    ip = x_forwarded_for.split(",")[0] if x_forwarded_for else request.META.get("REMOTE_ADDR")

    params = request.GET.dict()
    candidate_id =  params.get("candidate_id")

    try:
        candidate_instance = AccountsUserModel.objects.get(id=candidate_id)
    except AccountsUserModel.DoesNotExist:
        return False

    request_details = get_details_from_request(request=request)

    prev_request = EmployerTrackerModel.objects.filter(
        ip_address=ip,
        candidate=candidate_instance,
    ).exists()

    return prev_request

def create_tracking_instance(request):
    """Create a tracking instance in PostgreSQL"""
    
    params = request.GET.dict()
    candidate_id = params.get("candidate_id")

    try:
        candidate_instance = AccountsUserModel.objects.get(id=candidate_id)
    except AccountsUserModel.DoesNotExist:
        return {"message": "Invalid candidate ID"}

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    ip_address = x_forwarded_for.split(",")[0] if x_forwarded_for else request.META.get("REMOTE_ADDR")

    request_details = get_details_from_request(request=request)

    final_data = {
        **request_details,
        **params,
        "created_at": datetime.datetime.now(pytz.utc),
        "ip_address": ip_address,
        "candidate": candidate_instance,
    }

    tracking_instance = EmployerTrackerModel.objects.create(**final_data)

    return {
        "message": "Tracking data saved successfully",
        "tracking_id": str(tracking_instance.id)
    }