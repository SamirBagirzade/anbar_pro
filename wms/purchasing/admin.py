from django.contrib import admin
from .models import PurchaseHeader, PurchaseLine, PurchaseAttachment


class PurchaseLineInline(admin.TabularInline):
    model = PurchaseLine
    extra = 1


class PurchaseAttachmentInline(admin.TabularInline):
    model = PurchaseAttachment
    extra = 0


@admin.register(PurchaseHeader)
class PurchaseHeaderAdmin(admin.ModelAdmin):
    list_display = ("vendor", "warehouse", "invoice_no", "invoice_date", "is_posted")
    inlines = [PurchaseLineInline, PurchaseAttachmentInline]
