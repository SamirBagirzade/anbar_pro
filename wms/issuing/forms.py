from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory
from .models import IssueHeader, IssueLine
from wms.masters.models import Item


class ItemSelectWithUnit(forms.Select):
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
    item_name = forms.CharField(required=False, label=_("Item"))

    class Meta:
        model = IssueLine
        fields = ["item", "qty"]
        labels = {"item": _("Item"), "qty": _("Qty")}
        widgets = {"item": ItemSelectWithUnit()}

    def __init__(self, *args, warehouse_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["item"].required = False
        self.fields["item"].widget = ItemSelectWithUnit()
        self.fields["item"].label_from_instance = lambda obj: obj.name

        self.initial_item_unit = ""
        if self.instance and self.instance.pk and self.instance.item_id:
            self.initial_item_unit = self.instance.item.unit or ""
            self.initial["item_name"] = self.instance.item.name
        else:
            initial_item_id = self.initial.get("item")
            if initial_item_id:
                try:
                    item_id = int(initial_item_id)
                    item = Item.objects.filter(pk=item_id).only("unit", "name").first()
                    if item:
                        self.initial_item_unit = item.unit or ""
                        self.initial["item_name"] = item.name
                except (TypeError, ValueError):
                    pass

    def clean(self):
        cleaned = super().clean()
        item = cleaned.get("item")
        item_name = (cleaned.get("item_name") or "").strip()
        qty = cleaned.get("qty")

        if not item and item_name:
            item = Item.objects.filter(name__iexact=item_name).first()
            if item:
                cleaned["item"] = item
            else:
                self.add_error("item_name", _("No item found with that name. Pick one from the list."))

        if not item and not item_name and qty is not None:
            self.add_error("item", _("Item is required."))

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
