from django.db import models
from django.conf import settings
from wms.masters.models import Vendor, Warehouse, Item


def purchase_attachment_path(instance, filename: str) -> str:
    return f"purchase_attachments/{instance.purchase_id}/{filename}"


class PurchaseHeader(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    invoice_no = models.CharField(max_length=100, blank=True)
    invoice_date = models.DateField()
    currency = models.CharField(max_length=10, default=settings.DEFAULT_CURRENCY)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_posted = models.BooleanField(default=False)
    posted_at = models.DateTimeField(blank=True, null=True)


class PurchaseLine(models.Model):
    purchase = models.ForeignKey(PurchaseHeader, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=14, decimal_places=3)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    discount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=14, decimal_places=2)


class PurchaseAttachment(models.Model):
    purchase = models.ForeignKey(PurchaseHeader, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to=purchase_attachment_path)
    original_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)
