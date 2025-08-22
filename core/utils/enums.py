"""Enums"""

from core.utils.generic_enum_utils import EnumChoices

class UserTypeEnum(EnumChoices):
    """User Type Enum"""

    ADMIN = "ADMIN"
    EMPLOYER = "EMPLOYER"
    CANDIDATE = "CANDIDATE"

class JobsJobTypeEnum(EnumChoices):
    """Job Types Enum"""
    FULL_TIME = "FULL_TIME"
    INTERSHIP = "INTERNSHIP"
    CONTRACT = "CONTRACT"

class JobStatusTypeEnum(EnumChoices):
    DEACTIVATED = "DEACTIVATED" 
    PAUSED = "PAUSED"
    ACTIVATED = "ACTIVATED"
    DRAFTED = "DRAFTED"

class JobSalaryPeriodTypeEnum(EnumChoices):
    YEARLY = "YEARLY" 
    MONTHLY = "MONTHLY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"


class ApplyJobAboutThisJobTypeEnum(EnumChoices):
    """How would you know about this job Type Enum"""

    CAREER_PAGE = "CAREER_PAGE"