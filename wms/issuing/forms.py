from django import forms
from django.forms import inlineformset_factory
from .models import IssueHeader, IssueLine


class IssueHeaderForm(forms.ModelForm):
    issue_date = forms.DateField(
        input_formats=["%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d"],
        widget=forms.DateInput(
            attrs={"type": "text", "placeholder": "dd/mm/yyyy", "inputmode": "numeric", "data-date-picker": "1"},
            format="%d/%m/%Y",
        ),
    )

    class Meta:
        model = IssueHeader
        fields = ["warehouse", "outgoing_location", "issue_date", "notes"]

    def __init__(self, *args, **kwargs):
        from django.utils import timezone
        super().__init__(*args, **kwargs)
        if not self.instance.pk and not self.initial.get("issue_date"):
            self.initial["issue_date"] = timezone.localdate()


class IssueLineForm(forms.ModelForm):
    class Meta:
        model = IssueLine
        fields = ["item", "qty"]


IssueLineFormSet = inlineformset_factory(
    IssueHeader,
    IssueLine,
    form=IssueLineForm,
    extra=3,
    can_delete=False,
)
