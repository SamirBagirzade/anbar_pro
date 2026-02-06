from django.db import models
from django.conf import settings
from wms.masters.models import Warehouse, OutgoingLocation, Item


class IssueHeader(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    outgoing_location = models.ForeignKey(OutgoingLocation, on_delete=models.PROTECT)
    issue_date = models.DateField()
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_posted = models.BooleanField(default=False)
    posted_at = models.DateTimeField(blank=True, null=True)


class IssueLine(models.Model):
    header = models.ForeignKey(IssueHeader, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=14, decimal_places=3)


class IssueAttachment(models.Model):
    header = models.ForeignKey(IssueHeader, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="issue_attachments/%Y/%m/%d/")
    original_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)
