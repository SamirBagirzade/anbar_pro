from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory
from decimal import Decimal
from .models import PurchaseHeader, PurchaseLine, PurchaseAttachment
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
    class Meta:
        model = PurchaseLine
        fields = ["item", "qty", "unit_price", "discount", "tax_rate"]
        labels = {
            "item": _("Item"),
            "qty": _("Qty"),
            "unit_price": _("Unit Price"),
            "discount": _("Discount"),
            "tax_rate": _("Tax Rate"),
        }

    def clean(self):
        cleaned = super().clean()
        qty = cleaned.get("qty") or Decimal("0")
        unit_price = cleaned.get("unit_price") or Decimal("0")
        discount = cleaned.get("discount") or Decimal("0")
        tax_rate = cleaned.get("tax_rate") or Decimal("0")
        qty = quantize_qty(qty)
        unit_price = quantize_money(unit_price)
        discount = quantize_money(discount)
        tax_multiplier = Decimal("1") + (tax_rate / Decimal("100"))
        line_total = quantize_money((qty * unit_price - discount) * tax_multiplier)
        cleaned["line_total"] = line_total
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
