


from accounts.models import AccountsUserModel

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
    job_id =  params.get("job_id")

    try:
        job_instance = EmployerJobDetailsModel.objects.get(id=job_id)
    except EmployerJobDetailsModel.DoesNotExist:
        return False

    request_details = get_details_from_request(request=request)

    prev_request = EmployerTrackerModel.objects.filter(
        ip_address=ip,
        job=job_instance,
    ).exists()

    return prev_request

def create_tracking_instance(request):
    """Create a tracking instance in PostgreSQL"""
    
    params = request.GET.dict()
    job_id = params.get("job_id")

    try:
        job_instance = EmployerJobDetailsModel.objects.get(id=job_id)
    except EmployerJobDetailsModel.DoesNotExist:
        return {"message": "Invalid job ID"}

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    ip_address = x_forwarded_for.split(",")[0] if x_forwarded_for else request.META.get("REMOTE_ADDR")

    request_details = get_details_from_request(request=request)

    final_data = {
        **request_details,
        **params,
        "created_at": datetime.datetime.now(pytz.utc),
        "ip_address": ip_address,
        "job": job_instance,
    }

    tracking_instance = EmployerTrackerModel.objects.create(**final_data)

    return {
        "message": "Tracking data saved successfully",
        "tracking_id": str(tracking_instance.id)
    }   