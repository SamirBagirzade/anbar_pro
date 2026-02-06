from django.contrib import admin
from .models import StockBalance, StockMovement, TransferHeader, TransferLine, AdjustmentHeader, AdjustmentLine


@admin.register(StockBalance)
class StockBalanceAdmin(admin.ModelAdmin):
    list_display = ("warehouse", "item", "on_hand")
    search_fields = ("warehouse__name", "item__name")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("movement_type", "warehouse", "item", "qty_delta", "created_at")
    search_fields = ("warehouse__name", "item__name")
    readonly_fields = [field.name for field in StockMovement._meta.fields]


class TransferLineInline(admin.TabularInline):
    model = TransferLine
    extra = 1


@admin.register(TransferHeader)
class TransferHeaderAdmin(admin.ModelAdmin):
    list_display = ("from_warehouse", "to_warehouse", "date", "is_posted")
    inlines = [TransferLineInline]


class AdjustmentLineInline(admin.TabularInline):
    model = AdjustmentLine
    extra = 1


@admin.register(AdjustmentHeader)
class AdjustmentHeaderAdmin(admin.ModelAdmin):
    list_display = ("warehouse", "date", "reason", "is_posted")
    inlines = [AdjustmentLineInline]
