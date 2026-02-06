from django import forms
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


class VendorAttachmentForm(forms.ModelForm):
    class Meta:
        model = VendorAttachment
        fields = ["file"]


class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ["name", "location", "notes", "is_active"]


class OutgoingLocationForm(forms.ModelForm):
    class Meta:
        model = OutgoingLocation
        fields = ["name", "type", "notes", "is_active"]


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


class ItemInitialStockForm(forms.Form):
    vendor = forms.ModelChoiceField(queryset=Vendor.objects.filter(is_active=True))
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.filter(is_active=True))
    qty = forms.DecimalField(max_digits=14, decimal_places=3)
    unit_price = forms.DecimalField(max_digits=14, decimal_places=2)
    currency = forms.CharField(max_length=10, initial="AZN")
    attachments = forms.FileField(
        required=False,
        widget=MultiFileInput(attrs={"multiple": True}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        first_wh = Warehouse.objects.filter(is_active=True).order_by("name").first()
        if first_wh and not self.initial.get("warehouse"):
            self.initial["warehouse"] = first_wh
