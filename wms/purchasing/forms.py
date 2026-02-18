from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory
from decimal import Decimal
from .models import PurchaseHeader, PurchaseLine, PurchaseAttachment
from wms.masters.models import Item, Unit
from wms.inventory.services import quantize_money, quantize_qty


class PurchaseHeaderForm(forms.ModelForm):
    invoice_date = forms.DateField(
        label=_("Invoice Date"),
        input_formats=["%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d"],
        widget=forms.DateInput(
            attrs={"type": "text", "placeholder": "dd/mm/yyyy", "inputmode": "numeric", "data-date-picker": "1"},
            format="%d/%m/%Y",
        ),
    )

    class Meta:
        model = PurchaseHeader
        fields = ["vendor", "warehouse", "invoice_date", "currency", "notes"]
        labels = {
            "vendor": _("Vendor"),
            "warehouse": _("Warehouse"),
            "currency": _("Currency"),
            "notes": _("Notes"),
        }

    def __init__(self, *args, **kwargs):
        from django.utils import timezone

        super().__init__(*args, **kwargs)
        if not self.instance.pk and not self.initial.get("invoice_date"):
            self.initial["invoice_date"] = timezone.localdate()


class PurchaseLineForm(forms.ModelForm):
    item_name = forms.CharField(required=False, label=_("Item"))
    unit = forms.ChoiceField(required=False, label=_("Unit"))

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
        self.fields["unit_price"].required = False
        self.fields["item"].label_from_instance = lambda obj: obj.name
        units = list(Unit.objects.filter(is_active=True).order_by("name").values_list("name", flat=True))
        current_unit = (self.initial.get("unit") or "").strip()
        if not current_unit and self.instance and self.instance.pk:
            current_unit = (self.instance.item.unit or "").strip() if self.instance.item else ""
        if current_unit:
            self.initial["unit"] = current_unit
            self.fields["unit"].initial = current_unit
        if current_unit and current_unit not in units:
            units.append(current_unit)
            units.sort(key=str.lower)
        self.fields["unit"].choices = [("", "---------")] + [(unit, unit) for unit in units]
        self.fields["unit"].widget.attrs.update({"class": "form-control form-control-sm"})

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
        cleaned["unit_price"] = unit_price
        discount = Decimal("0")
        tax_multiplier = Decimal("1") + (tax_rate / Decimal("100"))
        line_total = quantize_money((qty * unit_price - discount) * tax_multiplier)
        cleaned["line_total"] = line_total
        if unit and not Unit.objects.filter(name__iexact=unit, is_active=True).exists():
            self.add_error("unit", _("Select a valid unit from the unit list."))

        normalized_item_name = item_name
        if normalized_item_name and " - " in normalized_item_name:
            # If UI text was sent as "ITEM-000123 - Name", keep only the real item name.
            normalized_item_name = normalized_item_name.split(" - ", 1)[1].strip() or normalized_item_name
        cleaned["item_name"] = normalized_item_name

        if not item and item_name:
            existing = Item.objects.filter(name__iexact=normalized_item_name).first()
            if existing:
                cleaned["resolved_item"] = existing
            elif not unit:
                self.add_error("unit", _("Unit is required for new items."))
        return cleaned


PurchaseLineFormSet = inlineformset_factory(
    PurchaseHeader,
    PurchaseLine,
    form=PurchaseLineForm,
    extra=10,
    can_delete=True,
)


class PurchaseAttachmentForm(forms.ModelForm):
    class Meta:
        model = PurchaseAttachment
        fields = ["file"]
        labels = {"file": _("File")}
