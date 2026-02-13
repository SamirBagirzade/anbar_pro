from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from wms.inventory.models import StockBalance, StockMovement, TransferHeader, AdjustmentHeader
from wms.purchasing.models import PurchaseHeader
from wms.issuing.models import IssueHeader


def quantize_qty(value: Decimal) -> Decimal:
    return value.quantize(Decimal(settings.QUANT_QTY), rounding=ROUND_HALF_UP)


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal(settings.QUANT_MONEY), rounding=ROUND_HALF_UP)


@transaction.atomic
def apply_movement(*, user, warehouse, item, qty_delta, movement_type, unit_cost=None, currency=None,
                   reference_type="", reference_id=None, note="", override_reason=""):
    qty_delta = quantize_qty(Decimal(qty_delta))
    if qty_delta == 0:
        return None

    balance, _ = StockBalance.objects.select_for_update().get_or_create(
        warehouse=warehouse, item=item, defaults={"on_hand": Decimal("0")}
    )

    new_on_hand = quantize_qty(balance.on_hand + qty_delta)
    override_negative = False

    if new_on_hand < 0:
        if user.is_superuser or user.has_perm("inventory.override_negative_stock"):
            override_negative = True
        else:
            raise PermissionDenied("Insufficient stock and no override permission")

    balance.on_hand = new_on_hand
    balance.save(update_fields=["on_hand"])

    movement = StockMovement.objects.create(
        warehouse=warehouse,
        item=item,
        movement_type=movement_type,
        qty_delta=qty_delta,
        unit_cost=unit_cost,
        currency=currency or settings.DEFAULT_CURRENCY,
        reference_type=reference_type,
        reference_id=reference_id,
        note=note,
        override_negative=override_negative,
        override_reason=override_reason if override_negative else "",
        created_by=user,
    )
    return movement


@transaction.atomic
def post_purchase(purchase: PurchaseHeader, user, override_reason=""):
    if purchase.is_posted:
        return purchase

    purchase = PurchaseHeader.objects.select_for_update().get(pk=purchase.pk)
    if purchase.is_posted:
        return purchase

    for line in purchase.lines.select_related("item"):
        apply_movement(
            user=user,
            warehouse=purchase.warehouse,
            item=line.item,
            qty_delta=line.qty,
            movement_type=StockMovement.TYPE_IN_PURCHASE,
            unit_cost=line.unit_price,
            currency=purchase.currency,
            reference_type="purchase",
            reference_id=purchase.id,
            note=f"Invoice {purchase.invoice_no}",
            override_reason=override_reason,
        )

    purchase.is_posted = True
    purchase.posted_at = timezone.now()
    purchase.save(update_fields=["is_posted", "posted_at"])
    return purchase


@transaction.atomic
def post_issue(issue: IssueHeader, user, override_reason=""):
    if issue.is_posted:
        return issue

    issue = IssueHeader.objects.select_for_update().get(pk=issue.pk)
    if issue.is_posted:
        return issue

    for line in issue.lines.select_related("item"):
        apply_movement(
            user=user,
            warehouse=issue.warehouse,
            item=line.item,
            qty_delta=-abs(line.qty),
            movement_type=StockMovement.TYPE_OUT_ISSUE,
            unit_cost=None,
            currency=settings.DEFAULT_CURRENCY,
            reference_type="issue",
            reference_id=issue.id,
            note=f"Issue to {issue.outgoing_location}",
            override_reason=override_reason,
        )

    issue.is_posted = True
    issue.posted_at = timezone.now()
    issue.save(update_fields=["is_posted", "posted_at"])
    return issue


@transaction.atomic
def post_transfer(transfer: TransferHeader, user, override_reason=""):
    if transfer.is_posted:
        return transfer

    transfer = TransferHeader.objects.select_for_update().get(pk=transfer.pk)
    if transfer.is_posted:
        return transfer

    for line in transfer.lines.select_related("item"):
        apply_movement(
            user=user,
            warehouse=transfer.from_warehouse,
            item=line.item,
            qty_delta=-abs(line.qty),
            movement_type=StockMovement.TYPE_TRANSFER_OUT,
            unit_cost=None,
            currency=settings.DEFAULT_CURRENCY,
            reference_type="transfer",
            reference_id=transfer.id,
            note=f"Transfer to {transfer.to_warehouse}",
            override_reason=override_reason,
        )
        apply_movement(
            user=user,
            warehouse=transfer.to_warehouse,
            item=line.item,
            qty_delta=abs(line.qty),
            movement_type=StockMovement.TYPE_TRANSFER_IN,
            unit_cost=None,
            currency=settings.DEFAULT_CURRENCY,
            reference_type="transfer",
            reference_id=transfer.id,
            note=f"Transfer from {transfer.from_warehouse}",
            override_reason=override_reason,
        )

    transfer.is_posted = True
    transfer.posted_at = timezone.now()
    transfer.save(update_fields=["is_posted", "posted_at"])
    return transfer


@transaction.atomic
def post_adjustment(adjustment: AdjustmentHeader, user, override_reason=""):
    if adjustment.is_posted:
        return adjustment

    adjustment = AdjustmentHeader.objects.select_for_update().get(pk=adjustment.pk)
    if adjustment.is_posted:
        return adjustment

    for line in adjustment.lines.select_related("item"):
        apply_movement(
            user=user,
            warehouse=adjustment.warehouse,
            item=line.item,
            qty_delta=line.qty_delta,
            movement_type=StockMovement.TYPE_ADJUSTMENT,
            unit_cost=None,
            currency=settings.DEFAULT_CURRENCY,
            reference_type="adjustment",
            reference_id=adjustment.id,
            note=adjustment.reason,
            override_reason=override_reason,
        )

    adjustment.is_posted = True
    adjustment.posted_at = timezone.now()
    adjustment.save(update_fields=["is_posted", "posted_at"])
    return adjustment


@transaction.atomic
def delete_purchase_with_inventory(purchase: PurchaseHeader):
    purchase = PurchaseHeader.objects.select_for_update().get(pk=purchase.pk)
    purchase_item_ids = list(purchase.lines.values_list("item_id", flat=True).distinct())

    if purchase.is_posted:
        item_qty = defaultdict(Decimal)
        movements = StockMovement.objects.select_for_update().filter(
            reference_type="purchase",
            reference_id=purchase.id,
            movement_type=StockMovement.TYPE_IN_PURCHASE,
        )

        has_movements = movements.exists()
        if has_movements:
            for movement in movements.select_related("item"):
                item_qty[movement.item_id] += movement.qty_delta
        else:
            for line in purchase.lines.select_related("item"):
                item_qty[line.item_id] += line.qty

        for item_id, qty in item_qty.items():
            balance, _ = StockBalance.objects.select_for_update().get_or_create(
                warehouse=purchase.warehouse,
                item_id=item_id,
                defaults={"on_hand": Decimal("0")},
            )
            balance.on_hand = quantize_qty(balance.on_hand - quantize_qty(qty))
            balance.save(update_fields=["on_hand"])

        if has_movements:
            movements.delete()

    purchase.delete()

    # Hide/remove items that only existed because of this deleted invoice.
    # Keep items that are still referenced by another transaction.
    if purchase_item_ids:
        from wms.masters.models import Item, VendorItem
        from wms.purchasing.models import PurchaseLine
        from wms.issuing.models import IssueLine
        from wms.inventory.models import TransferLine, AdjustmentLine

        for item_id in purchase_item_ids:
            has_other_purchase = PurchaseLine.objects.filter(item_id=item_id).exists()
            has_issue = IssueLine.objects.filter(item_id=item_id).exists()
            has_transfer = TransferLine.objects.filter(item_id=item_id).exists()
            has_adjustment = AdjustmentLine.objects.filter(item_id=item_id).exists()
            has_movements = StockMovement.objects.filter(item_id=item_id).exists()
            has_vendor_item = VendorItem.objects.filter(item_id=item_id).exists()

            if any([has_other_purchase, has_issue, has_transfer, has_adjustment, has_movements, has_vendor_item]):
                continue

            # Remove zero balances if any, then deactivate item so it disappears from stock pages.
            StockBalance.objects.filter(item_id=item_id, on_hand=Decimal("0")).delete()
            Item.objects.filter(pk=item_id).update(is_active=False)


@transaction.atomic
def delete_issue_with_inventory(issue: IssueHeader):
    issue = IssueHeader.objects.select_for_update().get(pk=issue.pk)

    if issue.is_posted:
        item_qty = defaultdict(Decimal)
        movements = StockMovement.objects.select_for_update().filter(
            reference_type="issue",
            reference_id=issue.id,
            movement_type=StockMovement.TYPE_OUT_ISSUE,
        )

        has_movements = movements.exists()
        if has_movements:
            for movement in movements.select_related("item"):
                item_qty[movement.item_id] += abs(movement.qty_delta)
        else:
            for line in issue.lines.select_related("item"):
                item_qty[line.item_id] += line.qty

        for item_id, qty in item_qty.items():
            balance, _ = StockBalance.objects.select_for_update().get_or_create(
                warehouse=issue.warehouse,
                item_id=item_id,
                defaults={"on_hand": Decimal("0")},
            )
            balance.on_hand = quantize_qty(balance.on_hand + quantize_qty(qty))
            balance.save(update_fields=["on_hand"])

        if has_movements:
            movements.delete()

    issue.delete()


@transaction.atomic
def unpost_purchase_inventory(purchase: PurchaseHeader):
    purchase = PurchaseHeader.objects.select_for_update().get(pk=purchase.pk)
    if not purchase.is_posted:
        return

    item_qty_by_wh = defaultdict(Decimal)
    movements = StockMovement.objects.select_for_update().filter(
        reference_type="purchase",
        reference_id=purchase.id,
        movement_type=StockMovement.TYPE_IN_PURCHASE,
    )

    has_movements = movements.exists()
    if has_movements:
        for movement in movements.select_related("item", "warehouse"):
            key = (movement.warehouse_id, movement.item_id)
            item_qty_by_wh[key] += movement.qty_delta
    else:
        for line in purchase.lines.select_related("item"):
            key = (purchase.warehouse_id, line.item_id)
            item_qty_by_wh[key] += line.qty

    for (warehouse_id, item_id), qty in item_qty_by_wh.items():
        balance, _ = StockBalance.objects.select_for_update().get_or_create(
            warehouse_id=warehouse_id,
            item_id=item_id,
            defaults={"on_hand": Decimal("0")},
        )
        balance.on_hand = quantize_qty(balance.on_hand - quantize_qty(qty))
        balance.save(update_fields=["on_hand"])

    if has_movements:
        movements.delete()

    purchase.is_posted = False
    purchase.posted_at = None
    purchase.save(update_fields=["is_posted", "posted_at"])
