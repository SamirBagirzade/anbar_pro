from django.db import models
from django.conf import settings
from wms.masters.models import Warehouse, Item


class StockMovement(models.Model):
    TYPE_IN_PURCHASE = "IN_PURCHASE"
    TYPE_OUT_ISSUE = "OUT_ISSUE"
    TYPE_TRANSFER_IN = "TRANSFER_IN"
    TYPE_TRANSFER_OUT = "TRANSFER_OUT"
    TYPE_ADJUSTMENT = "ADJUSTMENT"

    MOVEMENT_TYPES = [
        (TYPE_IN_PURCHASE, "In Purchase"),
        (TYPE_OUT_ISSUE, "Out Issue"),
        (TYPE_TRANSFER_IN, "Transfer In"),
        (TYPE_TRANSFER_OUT, "Transfer Out"),
        (TYPE_ADJUSTMENT, "Adjustment"),
    ]

    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    movement_type = models.CharField(max_length=30, choices=MOVEMENT_TYPES)
    qty_delta = models.DecimalField(max_digits=14, decimal_places=3)
    unit_cost = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=10, default=settings.DEFAULT_CURRENCY)
    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.PositiveIntegerField(blank=True, null=True)
    note = models.TextField(blank=True)
    override_negative = models.BooleanField(default=False)
    override_reason = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["warehouse", "item"]),
            models.Index(fields=["created_at"]),
        ]
        permissions = [
            ("override_negative_stock", "Can override negative stock"),
        ]


class StockBalance(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    on_hand = models.DecimalField(max_digits=14, decimal_places=3, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["warehouse", "item"], name="uq_stock_balance_wh_item")
        ]
        indexes = [models.Index(fields=["warehouse", "item"])]


class TransferHeader(models.Model):
    from_warehouse = models.ForeignKey(Warehouse, related_name="transfers_out", on_delete=models.PROTECT)
    to_warehouse = models.ForeignKey(Warehouse, related_name="transfers_in", on_delete=models.PROTECT)
    date = models.DateField()
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_posted = models.BooleanField(default=False)
    posted_at = models.DateTimeField(blank=True, null=True)


class TransferLine(models.Model):
    header = models.ForeignKey(TransferHeader, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=14, decimal_places=3)


class AdjustmentHeader(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    date = models.DateField()
    reason = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_posted = models.BooleanField(default=False)
    posted_at = models.DateTimeField(blank=True, null=True)


class AdjustmentLine(models.Model):
    header = models.ForeignKey(AdjustmentHeader, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    qty_delta = models.DecimalField(max_digits=14, decimal_places=3)
