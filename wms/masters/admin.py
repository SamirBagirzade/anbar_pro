from django.contrib import admin
from .models import Vendor, Warehouse, OutgoingLocation, Unit, Item, VendorItem, VendorAttachment


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_person", "phone", "email", "is_active")
    search_fields = ("name", "contact_person", "phone", "email")


@admin.register(VendorAttachment)
class VendorAttachmentAdmin(admin.ModelAdmin):
    list_display = ("vendor", "original_name", "file_type", "uploaded_at", "uploaded_by")


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "is_active")
    search_fields = ("name", "location")


@admin.register(OutgoingLocation)
class OutgoingLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "is_active")
    search_fields = ("name",)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    search_fields = ("name",)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "unit", "min_stock", "is_active")
    search_fields = ("name", "category")


@admin.register(VendorItem)
class VendorItemAdmin(admin.ModelAdmin):
    list_display = ("vendor", "item", "vendor_part_number", "preferred")
    search_fields = ("vendor__name", "item__name", "vendor_part_number")
