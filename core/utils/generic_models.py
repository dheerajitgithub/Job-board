"""Generic Model for all project models"""

from django.db import models

class CoreGenericModel(models.Model):
    """
        This class is inherited by all models throught the application
    """
    created_at = models.DateTimeField(auto_now_add=True,
                                      null=True)
    updated_at = models.DateTimeField(auto_now_add=True,
                                      null=True)
    
    class Meta:
        """Meta properties"""

        abstract = True