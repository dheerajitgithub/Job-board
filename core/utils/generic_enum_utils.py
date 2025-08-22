"""Generic enum classes"""

import enum


class EnumChoices(enum.Enum):
    """Base Enum Choice Class"""
    @classmethod
    def choices(cls):
        """choices method"""
        return [(key.value,key.name) for key in cls]