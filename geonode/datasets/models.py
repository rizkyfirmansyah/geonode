from django.db import models

class Ropa(models.Model):
    """
    Table for record of processing activities
    When users request to download and use of classified data, this table holds information needed to record all requests
    """
    uuid = models.CharField(max_length=255)
    requester_name = models.CharField(max_length=255)
    requester_email = models.CharField(max_length=255)
    requester_position = models.CharField(max_length=255)
    requester_institution = models.CharField(max_length=255)
    purposes = models.TextField(default='')
    retention = models.CharField(blank=True, max_length=255)
    resource_title = models.CharField(max_length=255)
    resource_owner_id = models.IntegerField(null=False)
    resource_owner = models.CharField(max_length=255)

    def __str__(self):
        return self.resource_title

    class Meta:
        ordering = ["id"]
        verbose_name_plural = "Record of Processing Activities"