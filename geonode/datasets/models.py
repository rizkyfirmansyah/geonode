from django.db import models

"""
Table for record of processing activities
When users request to download and use of classified data, this table holds information needed to record all requests
"""
class Ropa(models.Model):
    """

    """
    identifier = models.CharField(max_length=255)
    requester_name = models.CharField(max_length=255)
    requester_email = models.CharField(max_length=255)
    requester_position = models.CharField(max_length=255)
    requester_institution = models.CharField(max_length=255)
    purposes = models.TextField(default='')
    retention = models.CharField(max_length=255)
    resourcebase_ptr_id = models.IntegerField()
    resource_title = models.CharField(max_length=255)
    resource_name = models.CharField(max_length=255)
    resource_owner = models.CharField(max_length=255)

    def __str__(self):
        return self.resource_title

    class Meta:
        ordering = ("identifier",)
        verbose_name_plural = "Record of Processing Activities"