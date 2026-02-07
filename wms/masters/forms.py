from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Vendor, Warehouse, OutgoingLocation, Item, VendorAttachment
from django.utils import timezone


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True



class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = [
            "name",
            "contact_person",
            "phone",
            "email",
            "tax_id",
            "address",
            "notes",
            "is_active",
        ]
        labels = {
            "name": _("Name"),
            "contact_person": _("Contact Person"),
            "phone": _("Phone"),
            "email": _("Email"),
            "tax_id": _("Tax ID"),
            "address": _("Address"),
            "notes": _("Notes"),
            "is_active": _("Active"),
        }


class VendorAttachmentForm(forms.ModelForm):
    class Meta:
        model = VendorAttachment
        fields = ["file"]
        labels = {"file": _("File")}


class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ["name", "location", "notes", "is_active"]
        labels = {
            "name": _("Name"),
            "location": _("Location"),
            "notes": _("Notes"),
            "is_active": _("Active"),
        }


class OutgoingLocationForm(forms.ModelForm):
    class Meta:
        model = OutgoingLocation
        fields = ["name", "type", "notes", "is_active"]
        labels = {
            "name": _("Name"),
            "type": _("Type"),
            "notes": _("Notes"),
            "is_active": _("Active"),
        }


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            "name",
            "category",
            "unit",
            "min_stock",
            "notes",
            "is_active",
            "photo",
        ]
        labels = {
            "name": _("Name"),
            "category": _("Category"),
            "unit": _("Unit"),
            "min_stock": _("Minimum Stock"),
            "notes": _("Notes"),
            "is_active": _("Active"),
            "photo": _("Photo"),
        }


class ItemInitialStockForm(forms.Form):
    vendor = forms.ModelChoiceField(queryset=Vendor.objects.filter(is_active=True), label=_("Vendor"))
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.filter(is_active=True), label=_("Warehouse"))
    qty = forms.DecimalField(max_digits=14, decimal_places=3, label=_("Qty"))
    unit_price = forms.DecimalField(max_digits=14, decimal_places=2, label=_("Unit Price"))
    currency = forms.CharField(max_length=10, initial="AZN", label=_("Currency"))
    attachments = forms.FileField(
        required=False,
        widget=MultiFileInput(attrs={"multiple": True}),
        label=_("Attachments"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        first_wh = Warehouse.objects.filter(is_active=True).order_by("name").first()
        if first_wh and not self.initial.get("warehouse"):
            self.initial["warehouse"] = first_wh
