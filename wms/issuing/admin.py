from django.contrib import admin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import IssueHeader, IssueLine
from wms.inventory.services import delete_issue_with_inventory


class IssueLineInline(admin.TabularInline):
    model = IssueLine
    extra = 1


@admin.register(IssueHeader)
class IssueHeaderAdmin(admin.ModelAdmin):
    list_display = ("warehouse", "outgoing_location", "issue_date", "is_posted")
    inlines = [IssueLineInline]
    actions = ["delete_selected_issues_safely"]

    @admin.action(permissions=["delete"], description=_("Delete selected issues"))
    def delete_selected_issues_safely(self, request, queryset):
        count = 0
        for issue in queryset:
            delete_issue_with_inventory(issue)
            count += 1
        self.message_user(
            request,
            _("Deleted %(count)s issue(s).") % {"count": count},
            level=messages.SUCCESS,
        )
