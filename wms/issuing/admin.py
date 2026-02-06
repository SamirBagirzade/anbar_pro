from django.contrib import admin
from .models import IssueHeader, IssueLine


class IssueLineInline(admin.TabularInline):
    model = IssueLine
    extra = 1


@admin.register(IssueHeader)
class IssueHeaderAdmin(admin.ModelAdmin):
    list_display = ("warehouse", "outgoing_location", "issue_date", "is_posted")
    inlines = [IssueLineInline]
