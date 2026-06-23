from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory
from .models import IssueHeader, IssueLine
from wms.masters.models import Item


class ItemSelectWithUnit(forms.Select):
    def __init__(self, *args, stock_map=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.stock_map = stock_map or {}

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        raw_value = option.get("value")
        if raw_value not in (None, "", "None"):
            try:
                item_id = int(raw_value)
            except (TypeError, ValueError):
                return option
            item_unit = Item.objects.filter(pk=item_id).values_list("unit", flat=True).first()
            if item_unit:
                option.setdefault("attrs", {})
                option["attrs"]["data-unit"] = item_unit
            on_hand = self.stock_map.get(item_id)
            if on_hand is not None:
                option.setdefault("attrs", {})
                option["attrs"]["data-on-hand"] = str(on_hand)
        return option


class IssueHeaderForm(forms.ModelForm):
    issue_date = forms.DateField(
        label=_("Issue Date"),
        input_formats=["%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d"],
        widget=forms.DateInput(
            attrs={"type": "text", "placeholder": "dd/mm/yyyy", "inputmode": "numeric", "data-date-picker": "1"},
            format="%d/%m/%Y",
        ),
    )

    class Meta:
        model = IssueHeader
        fields = ["warehouse", "outgoing_location", "issue_date", "notes"]
        labels = {
            "warehouse": _("Warehouse"),
            "outgoing_location": _("Outgoing Location"),
            "notes": _("Notes"),
        }

    def __init__(self, *args, **kwargs):
        from django.utils import timezone
        super().__init__(*args, **kwargs)
        if not self.instance.pk and not self.initial.get("issue_date"):
            self.initial["issue_date"] = timezone.localdate()


class IssueLineForm(forms.ModelForm):
    class Meta:
        model = IssueLine
        fields = ["item", "qty"]
        labels = {"item": _("Item"), "qty": _("Qty")}
        widgets = {"item": ItemSelectWithUnit()}

    def __init__(self, *args, warehouse_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        stock_map = {}
        if warehouse_id:
            from wms.inventory.models import StockBalance
            stock_map = dict(
                StockBalance.objects.filter(warehouse_id=warehouse_id)
                .values_list("item_id", "on_hand")
            )
        self.fields["item"].widget = ItemSelectWithUnit(stock_map=stock_map)
        self.fields["item"].label_from_instance = lambda obj: obj.name

        self.initial_item_unit = ""
        self.initial_item_on_hand = ""
        if self.instance and self.instance.pk and self.instance.item_id:
            self.initial_item_unit = self.instance.item.unit or ""
            if self.instance.item_id in stock_map:
                self.initial_item_on_hand = str(stock_map[self.instance.item_id])
        else:
            initial_item_id = self.initial.get("item")
            if initial_item_id:
                try:
                    item_id = int(initial_item_id)
                    self.initial_item_unit = (
                        Item.objects.filter(pk=item_id).values_list("unit", flat=True).first() or ""
                    )
                    if item_id in stock_map:
                        self.initial_item_on_hand = str(stock_map[item_id])
                except (TypeError, ValueError):
                    pass

    def clean(self):
        cleaned = super().clean()
        item = cleaned.get("item")
        qty = cleaned.get("qty")
        if item and qty is not None and qty <= 0:
            self.add_error("qty", _("Quantity must be greater than 0."))
        return cleaned


IssueLineFormSet = inlineformset_factory(
    IssueHeader,
    IssueLine,
    form=IssueLineForm,
    extra=3,
    can_delete=True,
)


def build_issue_create_formset(extra=3):
    return inlineformset_factory(
        IssueHeader,
        IssueLine,
        form=IssueLineForm,
        extra=extra,
        can_delete=True,
    )


IssueEditLineFormSet = inlineformset_factory(
    IssueHeader,
    IssueLine,
    form=IssueLineForm,
    extra=0,
    can_delete=True,
)
