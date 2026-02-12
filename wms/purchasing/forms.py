from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory
from decimal import Decimal
from .models import PurchaseHeader, PurchaseLine, PurchaseAttachment
from wms.masters.models import Item, Unit
from wms.inventory.services import quantize_money, quantize_qty


class PurchaseHeaderForm(forms.ModelForm):
    class Meta:
        model = PurchaseHeader
        fields = ["vendor", "warehouse", "currency", "notes"]
        labels = {
            "vendor": _("Vendor"),
            "warehouse": _("Warehouse"),
            "currency": _("Currency"),
            "notes": _("Notes"),
        }


class PurchaseLineForm(forms.ModelForm):
    item_name = forms.CharField(required=False, label=_("Item"))
    unit = forms.CharField(required=False, label=_("Unit"))

    class Meta:
        model = PurchaseLine
        fields = ["item", "qty", "unit_price"]
        labels = {
            "item": _("Item"),
            "qty": _("Qty"),
            "unit_price": _("Unit Price"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["item"].required = False

    def clean(self):
        cleaned = super().clean()
        item = cleaned.get("item")
        item_name = (cleaned.get("item_name") or "").strip()
        unit = (cleaned.get("unit") or "").strip()
        qty = cleaned.get("qty") or Decimal("0")
        unit_price = cleaned.get("unit_price") or Decimal("0")
        tax_rate = cleaned.get("tax_rate") or Decimal("0")
        qty = quantize_qty(qty)
        unit_price = quantize_money(unit_price)
        discount = Decimal("0")
        tax_multiplier = Decimal("1") + (tax_rate / Decimal("100"))
        line_total = quantize_money((qty * unit_price - discount) * tax_multiplier)
        cleaned["line_total"] = line_total
        if unit and not Unit.objects.filter(name__iexact=unit, is_active=True).exists():
            self.add_error("unit", _("Select a valid unit from the unit list."))
        if not item and item_name:
            existing = Item.objects.filter(name__iexact=item_name).first()
            if existing:
                cleaned["resolved_item"] = existing
            elif not unit:
                self.add_error("unit", _("Unit is required for new items."))
        return cleaned


PurchaseLineFormSet = inlineformset_factory(
    PurchaseHeader,
    PurchaseLine,
    form=PurchaseLineForm,
    extra=3,
    can_delete=False,
)


class PurchaseAttachmentForm(forms.ModelForm):
    class Meta:
        model = PurchaseAttachment
        fields = ["file"]
        labels = {"file": _("File")}
