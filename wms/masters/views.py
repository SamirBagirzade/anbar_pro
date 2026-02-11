from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from .models import Vendor, Warehouse, OutgoingLocation, Item, VendorAttachment
from .forms import VendorForm, WarehouseForm, OutgoingLocationForm, ItemForm, ItemInitialStockForm, VendorAttachmentForm
from django.utils import timezone
from wms.purchasing.models import PurchaseHeader, PurchaseLine, PurchaseAttachment
from wms.inventory.services import post_purchase, quantize_money, quantize_qty


@login_required
@permission_required("masters.view_vendor", raise_exception=True)
def vendor_list(request):
    vendors = Vendor.objects.order_by("name")
    return render(request, "masters/vendor_list.html", {"vendors": vendors})


@login_required
@permission_required("masters.add_vendor", raise_exception=True)
def vendor_create(request):
    if request.method == "POST":
        form = VendorForm(request.POST)
        attachment_form = VendorAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            vendor = form.save()
            for f in request.FILES.getlist("attachments"):
                VendorAttachment.objects.create(
                    vendor=vendor,
                    file=f,
                    original_name=f.name,
                    file_type=getattr(f, "content_type", ""),
                    uploaded_by=request.user,
                )
            return redirect("vendor_list")
    else:
        form = VendorForm()
        attachment_form = VendorAttachmentForm()
    return render(
        request,
        "masters/vendor_form.html",
        {"form": form, "attachment_form": attachment_form, "attachments": [], "title": _("New Vendor")},
    )


@login_required
@permission_required("masters.change_vendor", raise_exception=True)
def vendor_edit(request, vendor_id: int):
    vendor = get_object_or_404(Vendor, pk=vendor_id)
    if request.method == "POST":
        if request.POST.get("action") == "delete_attachment":
            attachment_id = request.POST.get("attachment_id")
            attachment = get_object_or_404(VendorAttachment, pk=attachment_id, vendor=vendor)
            attachment.delete()
            return redirect("vendor_edit", vendor_id=vendor.id)
        form = VendorForm(request.POST, instance=vendor)
        attachment_form = VendorAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            for f in request.FILES.getlist("attachments"):
                VendorAttachment.objects.create(
                    vendor=vendor,
                    file=f,
                    original_name=f.name,
                    file_type=getattr(f, "content_type", ""),
                    uploaded_by=request.user,
                )
            return redirect("vendor_list")
    else:
        form = VendorForm(instance=vendor)
        attachment_form = VendorAttachmentForm()
    attachments = vendor.attachments.order_by("-uploaded_at")
    return render(
        request,
        "masters/vendor_form.html",
        {"form": form, "attachment_form": attachment_form, "attachments": attachments, "title": _("Edit Vendor")},
    )


@login_required
@permission_required("masters.delete_vendor", raise_exception=True)
def vendor_delete(request, vendor_id: int):
    vendor = get_object_or_404(Vendor, pk=vendor_id)
    if request.method == "POST":
        force = request.POST.get("force") == "1"
        try:
            vendor.delete()
        except ProtectedError:
            if not force:
                messages.error(request, _("Vendor is referenced by transactions and cannot be deleted."))
            else:
                with transaction.atomic():
                    replacement_vendor, created_vendor = Vendor.objects.get_or_create(
                        name="Deleted Vendor",
                        defaults={
                            "notes": _("Auto-created placeholder for force-deleted vendors."),
                            "is_active": False,
                        },
                    )
                    if replacement_vendor.pk == vendor.pk:
                        suffix = 2
                        while Vendor.objects.filter(name=f"Deleted Vendor {suffix}").exists():
                            suffix += 1
                        replacement_vendor = Vendor.objects.create(
                            name=f"Deleted Vendor {suffix}",
                            notes=_("Auto-created placeholder for force-deleted vendors."),
                            is_active=False,
                        )
                    PurchaseHeader.objects.filter(vendor=vendor).update(vendor=replacement_vendor)
                    vendor.delete()
        return redirect("vendor_list")
    return render(
        request,
        "masters/confirm_delete.html",
        {
            "object": vendor,
            "cancel_url": "/masters/vendors/",
            "allow_force": True,
            "force_label": _("Force delete by moving related purchases to a placeholder vendor"),
        },
    )


@login_required
@permission_required("masters.view_warehouse", raise_exception=True)
def warehouse_list(request):
    warehouses = Warehouse.objects.order_by("name")
    return render(request, "masters/warehouse_list.html", {"warehouses": warehouses})


@login_required
@permission_required("masters.add_warehouse", raise_exception=True)
def warehouse_create(request):
    if request.method == "POST":
        form = WarehouseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("warehouse_list")
    else:
        form = WarehouseForm()
    return render(request, "masters/warehouse_form.html", {"form": form, "title": _("New Warehouse")})


@login_required
@permission_required("masters.change_warehouse", raise_exception=True)
def warehouse_edit(request, warehouse_id: int):
    warehouse = get_object_or_404(Warehouse, pk=warehouse_id)
    if request.method == "POST":
        form = WarehouseForm(request.POST, instance=warehouse)
        if form.is_valid():
            form.save()
            return redirect("warehouse_list")
    else:
        form = WarehouseForm(instance=warehouse)
    return render(request, "masters/warehouse_form.html", {"form": form, "title": _("Edit Warehouse")})


@login_required
@permission_required("masters.delete_warehouse", raise_exception=True)
def warehouse_delete(request, warehouse_id: int):
    warehouse = get_object_or_404(Warehouse, pk=warehouse_id)
    if request.method == "POST":
        warehouse.delete()
        return redirect("warehouse_list")
    return render(request, "masters/confirm_delete.html", {"object": warehouse, "cancel_url": "/masters/warehouses/"})


@login_required
@permission_required("masters.view_outgoinglocation", raise_exception=True)
def outgoing_location_list(request):
    locations = OutgoingLocation.objects.order_by("name")
    return render(request, "masters/outgoing_location_list.html", {"locations": locations})


@login_required
@permission_required("masters.add_outgoinglocation", raise_exception=True)
def outgoing_location_create(request):
    if request.method == "POST":
        form = OutgoingLocationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("outgoing_location_list")
    else:
        form = OutgoingLocationForm()
    return render(request, "masters/outgoing_location_form.html", {"form": form, "title": _("New Outgoing Location")})


@login_required
@permission_required("masters.change_outgoinglocation", raise_exception=True)
def outgoing_location_edit(request, location_id: int):
    location = get_object_or_404(OutgoingLocation, pk=location_id)
    if request.method == "POST":
        form = OutgoingLocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            return redirect("outgoing_location_list")
    else:
        form = OutgoingLocationForm(instance=location)
    return render(request, "masters/outgoing_location_form.html", {"form": form, "title": _("Edit Outgoing Location")})


@login_required
@permission_required("masters.delete_outgoinglocation", raise_exception=True)
def outgoing_location_delete(request, location_id: int):
    location = get_object_or_404(OutgoingLocation, pk=location_id)
    if request.method == "POST":
        force = request.POST.get("force") == "1"
        try:
            location.delete()
        except ProtectedError:
            if not force:
                messages.error(request, _("Outgoing location is referenced by transactions and cannot be deleted."))
            else:
                from wms.issuing.models import IssueHeader
                from wms.inventory.models import StockMovement, StockBalance

                with transaction.atomic():
                    issue_ids = list(
                        IssueHeader.objects.filter(outgoing_location=location).values_list("id", flat=True)
                    )
                    if issue_ids:
                        # Reverse stock impact from posted issue movements before deleting those issues.
                        issue_movements = StockMovement.objects.filter(
                            reference_type="issue",
                            reference_id__in=issue_ids,
                        ).select_related("warehouse", "item")
                        for mv in issue_movements:
                            balance, created_balance = StockBalance.objects.get_or_create(
                                warehouse=mv.warehouse,
                                item=mv.item,
                                defaults={"on_hand": 0},
                            )
                            balance.on_hand = quantize_qty(balance.on_hand - mv.qty_delta)
                            balance.save(update_fields=["on_hand"])
                        issue_movements.delete()
                        IssueHeader.objects.filter(id__in=issue_ids).delete()
                    location.delete()
        return redirect("outgoing_location_list")
    return render(
        request,
        "masters/confirm_delete.html",
        {
            "object": location,
            "cancel_url": "/masters/outgoing-locations/",
            "allow_force": True,
            "force_label": _("Force delete and remove related issues/movements"),
        },
    )


@login_required
@permission_required("masters.view_item", raise_exception=True)
def item_list(request):
    items = Item.objects.order_by("name")
    return render(request, "masters/item_list.html", {"items": items})


@login_required
@permission_required("masters.view_item", raise_exception=True)
def item_search(request):
    q = request.GET.get("q", "").strip()
    items = Item.objects.filter(is_active=True)
    if q:
        items = items.filter(name__icontains=q)
    items = items.order_by("name")[:20]
    return render(request, "masters/_item_search_list.html", {"items": items})


@login_required
@permission_required("masters.add_item", raise_exception=True)
def item_create(request):
    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES)
        stock_form = ItemInitialStockForm(request.POST, request.FILES)
        if form.is_valid() and stock_form.is_valid():
            item = form.save()
            stock = stock_form.cleaned_data
            purchase = PurchaseHeader.objects.create(
                vendor=stock["vendor"],
                warehouse=stock["warehouse"],
                invoice_no="",
                invoice_date=timezone.localdate(),
                currency=stock["currency"],
                notes=_("Auto purchase from item creation"),
                created_by=request.user,
            )
            qty = quantize_qty(stock["qty"])
            unit_price = quantize_money(stock["unit_price"])
            line_total = quantize_money(qty * unit_price)
            PurchaseLine.objects.create(
                purchase=purchase,
                item=item,
                qty=qty,
                unit_price=unit_price,
                discount=0,
                tax_rate=0,
                line_total=line_total,
            )
            for f in request.FILES.getlist("attachments"):
                PurchaseAttachment.objects.create(
                    purchase=purchase,
                    file=f,
                    original_name=f.name,
                    file_type=getattr(f, "content_type", ""),
                    uploaded_by=request.user,
                )
            post_purchase(purchase, request.user)
            return redirect("item_list")
    else:
        form = ItemForm()
        stock_form = ItemInitialStockForm()
    return render(request, "masters/item_form.html", {"form": form, "stock_form": stock_form, "title": _("New Item")})


@login_required
@permission_required("masters.change_item", raise_exception=True)
def item_edit(request, item_id: int):
    item = get_object_or_404(Item, pk=item_id)
    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            return redirect("item_list")
    else:
        form = ItemForm(instance=item)
    return render(request, "masters/item_form.html", {"form": form, "stock_form": None, "title": _("Edit Item")})


@login_required
@permission_required("masters.delete_item", raise_exception=True)
def item_delete(request, item_id: int):
    item = get_object_or_404(Item, pk=item_id)
    if request.method == "POST":
        force = request.POST.get("force") == "1"
        try:
            item.delete()
        except ProtectedError:
            if not force:
                messages.error(request, _("Item is referenced by transactions and cannot be deleted."))
            else:
                from wms.inventory.models import StockMovement, StockBalance, TransferLine, AdjustmentLine
                from wms.issuing.models import IssueLine
                from wms.purchasing.models import PurchaseLine
                from wms.masters.models import VendorItem

                with transaction.atomic():
                    StockMovement.objects.filter(item=item).delete()
                    StockBalance.objects.filter(item=item).delete()
                    IssueLine.objects.filter(item=item).delete()
                    PurchaseLine.objects.filter(item=item).delete()
                    TransferLine.objects.filter(item=item).delete()
                    AdjustmentLine.objects.filter(item=item).delete()
                    VendorItem.objects.filter(item=item).delete()
                    item.delete()
        return redirect("item_list")
    return render(
        request,
        "masters/confirm_delete.html",
        {"object": item, "cancel_url": "/masters/items/", "allow_force": True},
    )
