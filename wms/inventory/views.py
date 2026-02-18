from django.contrib.auth.decorators import login_required, permission_required
from django.db import models
from django.db.models import OuterRef, Subquery, Value, DecimalField, DateField
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
import csv
from datetime import datetime

from wms.masters.models import Item, Warehouse, Vendor
from wms.purchasing.models import PurchaseLine
from wms.issuing.models import IssueLine
from .models import StockBalance, StockMovement


def _parse_date(value: str):
    if not value:
        return None
    for fmt in ("%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


@login_required
@permission_required("masters.view_item", raise_exception=True)
def warehouse_stock(request):
    warehouses = Warehouse.objects.filter(is_active=True).order_by("name")
    selected_warehouse_id = request.GET.get("warehouse")
    if not selected_warehouse_id and warehouses.exists():
        selected_warehouse_id = str(warehouses.first().id)

    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    low_stock = request.GET.get("low_stock", "") == "1"
    sort = request.GET.get("sort", "name")
    direction = request.GET.get("direction", "asc")

    items = Item.objects.filter(is_active=True)
    if q:
        items = items.filter(models.Q(name__icontains=q))
    if category:
        items = items.filter(category__iexact=category)

    if selected_warehouse_id:
        stock_sub = StockBalance.objects.filter(
            warehouse_id=selected_warehouse_id, item_id=OuterRef("pk")
        ).values("on_hand")[:1]
        items = items.annotate(
            on_hand=Coalesce(
                Subquery(stock_sub, output_field=DecimalField(max_digits=14, decimal_places=3)),
                Value("0.000", output_field=DecimalField(max_digits=14, decimal_places=3)),
            )
        )
    else:
        items = items.annotate(on_hand=Value("0.000", output_field=DecimalField(max_digits=14, decimal_places=3)))

    last_purchase = PurchaseLine.objects.filter(item_id=OuterRef("pk")).order_by(
        "-purchase__invoice_date", "-id"
    )
    items = items.annotate(
        last_purchase_vendor=Subquery(last_purchase.values("purchase__vendor__name")[:1]),
        last_purchase_unit_price=Subquery(last_purchase.values("unit_price")[:1]),
        last_purchase_date=Subquery(last_purchase.values("purchase__invoice_date")[:1], output_field=DateField()),
    )

    last_issue = IssueLine.objects.filter(item_id=OuterRef("pk")).order_by("-header__issue_date", "-id")
    items = items.annotate(
        last_issue_date=Subquery(last_issue.values("header__issue_date")[:1], output_field=DateField())
    )

    if low_stock:
        items = items.filter(on_hand__lt=models.F("min_stock"))

    if sort in {
        "name",
        "category",
        "unit",
        "on_hand",
        "min_stock",
        "last_purchase_vendor",
        "last_purchase_unit_price",
        "last_purchase_date",
        "last_issue_date",
    }:
        prefix = "" if direction == "asc" else "-"
        items = items.order_by(f"{prefix}{sort}")

    if request.GET.get("export") == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=warehouse_stock.csv"
        writer = csv.writer(response)
        writer.writerow([
            "item_name",
            "category",
            "unit",
            "on_hand",
            "min_stock",
            "last_purchase_vendor",
            "last_purchase_unit_price",
            "last_purchase_date",
            "last_issue_date",
        ])
        for item in items:
            writer.writerow([
                item.name,
                item.category,
                item.unit,
                item.on_hand,
                item.min_stock,
                item.last_purchase_vendor,
                item.last_purchase_unit_price,
                item.last_purchase_date,
                item.last_issue_date,
            ])
        return response

    paginator = Paginator(items, 25)
    page = paginator.get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    base_query = params.urlencode()

    vendor_color_map = {v.name: v.color_hex for v in Vendor.objects.all()}
    for obj in page:
        obj.last_purchase_vendor_color = vendor_color_map.get(obj.last_purchase_vendor, "")

    context = {
        "warehouses": warehouses,
        "selected_warehouse_id": selected_warehouse_id,
        "items": page,
        "q": q,
        "category": category,
        "low_stock": low_stock,
        "sort": sort,
        "direction": direction,
        "base_query": base_query,
    }

    if request.headers.get("HX-Request"):
        return render(request, "inventory/_stock_table.html", context)

    return render(request, "inventory/warehouse_stock.html", context)


@login_required
@permission_required("masters.view_item", raise_exception=True)
def item_detail(request, item_id: int):
    item = get_object_or_404(Item, pk=item_id)
    warehouse_id = request.GET.get("warehouse")
    movement_type = request.GET.get("movement_type")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    date_from_parsed = _parse_date(date_from)
    date_to_parsed = _parse_date(date_to)

    stock_per_warehouse = StockBalance.objects.filter(item=item).select_related("warehouse")

    movements = StockMovement.objects.filter(item=item).select_related("warehouse", "created_by")
    if warehouse_id:
        movements = movements.filter(warehouse_id=warehouse_id)
    if movement_type:
        movements = movements.filter(movement_type=movement_type)
    if date_from_parsed:
        movements = movements.filter(created_at__date__gte=date_from_parsed)
    if date_to_parsed:
        movements = movements.filter(created_at__date__lte=date_to_parsed)
    movements = movements.order_by("-created_at")[:200]

    purchases = (
        PurchaseLine.objects.filter(item=item)
        .select_related("purchase", "purchase__vendor")
        .order_by("-purchase__invoice_date", "-id")[:10]
    )

    return render(
        request,
        "inventory/item_detail.html",
        {
            "item": item,
            "stock_per_warehouse": stock_per_warehouse,
            "movements": movements,
            "purchases": purchases,
        },
    )


@login_required
@permission_required("inventory.view_stockmovement", raise_exception=True)
def recent_movements(request):
    sort = request.GET.get("sort", "created_at")
    direction = request.GET.get("direction", "desc")
    allowed = {"created_at", "movement_type", "qty_delta", "warehouse__name", "item__name"}
    if sort not in allowed:
        sort = "created_at"
    prefix = "-" if direction == "desc" else ""

    warehouse_id = request.GET.get("warehouse", "")
    movement_type = request.GET.get("movement_type", "")
    q = request.GET.get("q", "").strip()
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")
    date_from_parsed = _parse_date(date_from)
    date_to_parsed = _parse_date(date_to)

    movements = StockMovement.objects.select_related("warehouse", "item")
    if warehouse_id:
        movements = movements.filter(warehouse_id=warehouse_id)
    if movement_type:
        movements = movements.filter(movement_type=movement_type)
    if q:
        movements = movements.filter(item__name__icontains=q)
    if date_from_parsed:
        movements = movements.filter(created_at__date__gte=date_from_parsed)
    if date_to_parsed:
        movements = movements.filter(created_at__date__lte=date_to_parsed)

    movements = movements.order_by(f"{prefix}{sort}")
    paginator = Paginator(movements, 50)
    page = paginator.get_page(request.GET.get("page"))

    params = request.GET.copy()
    params.pop("page", None)
    base_query = params.urlencode()

    return render(
        request,
        "inventory/recent_movements.html",
        {
            "movements": page,
            "sort": sort,
            "direction": direction,
            "base_query": base_query,
            "warehouses": Warehouse.objects.filter(is_active=True).order_by("name"),
            "movement_types": StockMovement.MOVEMENT_TYPES,
            "warehouse_id": warehouse_id,
            "movement_type": movement_type,
            "q": q,
            "date_from": date_from,
            "date_to": date_to,
        },
    )
