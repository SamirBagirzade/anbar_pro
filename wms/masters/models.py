from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import hashlib


class Vendor(models.Model):
    name = models.CharField(max_length=255, unique=True)
    contact_person = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    tax_id = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name

    @property
    def color_hex(self) -> str:
        digest = hashlib.md5(self.name.encode("utf-8")).hexdigest()
        return f"#{digest[:6]}"


def vendor_attachment_path(instance, filename: str) -> str:
    return f"vendor_attachments/{instance.vendor_id}/{filename}"


class Warehouse(models.Model):
    name = models.CharField(max_length=255, unique=True)
    location = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class OutgoingLocation(models.Model):
    TYPE_DEPARTMENT = "department"
    TYPE_PROJECT = "project"
    TYPE_CLIENT = "client"
    TYPE_CHOICES = [
        (TYPE_DEPARTMENT, _("Department")),
        (TYPE_PROJECT, _("Project")),
        (TYPE_CLIENT, _("Client")),
    ]

    name = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name

    @property
    def color_hex(self) -> str:
        digest = hashlib.md5(self.name.encode("utf-8")).hexdigest()
        return f"#{digest[:6]}"


class Unit(models.Model):
    name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class Item(models.Model):
    internal_code = models.CharField(max_length=100, unique=True, blank=True, null=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255, blank=True)
    unit = models.CharField(max_length=50)
    min_stock = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    photo = models.ImageField(upload_to="item_photos/", blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["internal_code"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self) -> str:
        if self.internal_code:
            return f"{self.internal_code} - {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.internal_code:
            self.internal_code = f"ITEM-{self.id:06d}"
            super().save(update_fields=["internal_code"])


class VendorItem(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    vendor_part_number = models.CharField(max_length=100, blank=True, null=True)
    preferred = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["vendor", "item", "vendor_part_number"],
                name="uq_vendor_item_part",
            )
        ]

    def __str__(self) -> str:
        return f"{self.vendor} - {self.item}"


class VendorAttachment(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to=vendor_attachment_path)
    original_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)
