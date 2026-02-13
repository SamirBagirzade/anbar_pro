from django.contrib import admin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import Vendor, Warehouse, OutgoingLocation, Unit, Item, VendorItem, VendorAttachment


class BulkDeleteActionMixin:
    actions = ["bulk_delete_selected"]

    @admin.action(permissions=["delete"], description=_("Delete selected records"))
    def bulk_delete_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(
            request,
            _("Deleted %(count)s record(s).") % {"count": count},
            level=messages.SUCCESS,
        )


@admin.register(Vendor)
class VendorAdmin(BulkDeleteActionMixin, admin.ModelAdmin):
    list_display = ("name", "contact_person", "phone", "email", "is_active")
    search_fields = ("name", "contact_person", "phone", "email")


@admin.register(VendorAttachment)
class VendorAttachmentAdmin(BulkDeleteActionMixin, admin.ModelAdmin):
    list_display = ("vendor", "original_name", "file_type", "uploaded_at", "uploaded_by")


@admin.register(Warehouse)
class WarehouseAdmin(BulkDeleteActionMixin, admin.ModelAdmin):
    list_display = ("name", "location", "is_active")
    search_fields = ("name", "location")


@admin.register(OutgoingLocation)
class OutgoingLocationAdmin(BulkDeleteActionMixin, admin.ModelAdmin):
    list_display = ("name", "type", "is_active")
    search_fields = ("name",)


@admin.register(Unit)
class UnitAdmin(BulkDeleteActionMixin, admin.ModelAdmin):
    list_display = ("name", "is_active")
    search_fields = ("name",)


@admin.register(Item)
class ItemAdmin(BulkDeleteActionMixin, admin.ModelAdmin):
    list_display = ("name", "category", "unit", "min_stock", "is_active")
    search_fields = ("name", "category")
    actions = ["bulk_delete_selected"]

    @admin.action(permissions=["change"], description=_("Delete selected records"))
    def bulk_delete_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(
            request,
            _("Deleted %(count)s record(s).") % {"count": count},
            level=messages.SUCCESS,
        )


@admin.register(VendorItem)
class VendorItemAdmin(BulkDeleteActionMixin, admin.ModelAdmin):
    list_display = ("vendor", "item", "vendor_part_number", "preferred")
    search_fields = ("vendor__name", "item__name", "vendor_part_number")
