from django.contrib import admin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import PurchaseHeader, PurchaseLine, PurchaseAttachment
from wms.inventory.services import delete_purchase_with_inventory


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
    actions = ["delete_selected_purchases_safely"]

    @admin.action(permissions=["delete"], description=_("Delete selected purchases"))
    def delete_selected_purchases_safely(self, request, queryset):
        count = 0
        for purchase in queryset:
            delete_purchase_with_inventory(purchase)
            count += 1
        self.message_user(
            request,
            _("Deleted %(count)s purchase(s).") % {"count": count},
            level=messages.SUCCESS,
        )
