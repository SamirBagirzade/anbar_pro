from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from datetime import datetime
from pathlib import Path

_ALLOWED_ATTACHMENT_EXTS = {".pdf", ".jpg", ".jpeg", ".png", ".xlsx", ".xls", ".doc", ".docx"}


def _parse_date(value):
    if not value:
        return None
    for fmt in ("%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None
from .forms import PurchaseHeaderForm, PurchaseLineFormSet, PurchaseEditLineFormSet
from .models import PurchaseAttachment, PurchaseLine
from wms.masters.models import Item
from wms.inventory.services import post_purchase, delete_purchase_with_inventory, unpost_purchase_inventory
from .models import PurchaseHeader


def _can_delete_purchase(user):
    return user.is_superuser or user.has_perm("purchasing.delete_purchaseheader")


def _save_purchase_lines(purchase, formset):
    purchase.lines.all().delete()
    for form in formset:
        if not form.cleaned_data or form.cleaned_data.get("DELETE"):
            continue
        item = form.cleaned_data.get("item")
        item_name = (form.cleaned_data.get("item_name") or "").strip()
        unit = (form.cleaned_data.get("unit") or "").strip()
        if not item and not item_name:
            continue
        if not item:
            item = form.cleaned_data.get("resolved_item")
            if not item:
                item = Item.objects.filter(name__iexact=item_name).first()
            if item:
                if unit and unit != item.unit:
                    item.unit = unit
                    item.save(update_fields=["unit"])
            else:
                item = Item.objects.create(name=item_name, unit=unit)
        else:
            if unit and unit != item.unit:
                item.unit = unit
                item.save(update_fields=["unit"])

        if item and not item.is_active:
            item.is_active = True
            item.save(update_fields=["is_active"])

        PurchaseLine.objects.create(
            purchase=purchase,
            item=item,
            qty=form.cleaned_data["qty"],
            unit_price=form.cleaned_data["unit_price"],
            discount=0,
            tax_rate=0,
            line_total=form.cleaned_data["line_total"],
        )


@login_required
@permission_required("purchasing.view_purchaseheader", raise_exception=True)
def purchase_list(request):
    if request.method == "POST":
        if not _can_delete_purchase(request.user):
            raise PermissionDenied
        purchase_id = request.POST.get("purchase_id")
        purchase = get_object_or_404(PurchaseHeader, pk=purchase_id)
        delete_purchase_with_inventory(purchase)
        return redirect("purchase_list")

    vendor_id = request.GET.get("vendor", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    date_from_parsed = _parse_date(date_from)
    date_to_parsed = _parse_date(date_to)

    purchases = (
        PurchaseHeader.objects.select_related("vendor", "warehouse")
        .annotate(line_count=Count("lines", distinct=True), total_amount=Sum("lines__line_total"))
        .order_by("-invoice_date", "-id")
    )
    if vendor_id:
        purchases = purchases.filter(vendor_id=vendor_id)
    if date_from_parsed:
        purchases = purchases.filter(invoice_date__gte=date_from_parsed)
    if date_to_parsed:
        purchases = purchases.filter(invoice_date__lte=date_to_parsed)

    from wms.masters.models import Vendor
    vendors = Vendor.objects.filter(is_active=True).order_by("name")
    return render(
        request,
        "purchasing/purchase_list.html",
        {
            "purchases": purchases,
            "can_delete_purchase": _can_delete_purchase(request.user),
            "can_change_purchase": request.user.has_perm("purchasing.change_purchaseheader"),
            "vendors": vendors,
            "selected_vendor_id": vendor_id,
            "date_from": date_from,
            "date_to": date_to,
        },
    )


@login_required
@permission_required("purchasing.add_purchaseheader", raise_exception=True)
@transaction.atomic
def purchase_create(request):
    item_id = request.GET.get("item")
    if request.method == "POST":
        header_form = PurchaseHeaderForm(request.POST)
        formset = PurchaseLineFormSet(request.POST)
        if header_form.is_valid() and formset.is_valid():
            purchase = header_form.save(commit=False)
            purchase.created_by = request.user
            if not purchase.invoice_date:
                purchase.invoice_date = timezone.localdate()
            purchase.save()
            formset.instance = purchase
            _save_purchase_lines(purchase, formset)
            for f in request.FILES.getlist("attachments"):
                if Path(f.name).suffix.lower() not in _ALLOWED_ATTACHMENT_EXTS:
                    messages.warning(request, _("File type not allowed, skipped: %(name)s") % {"name": f.name})
                    continue
                PurchaseAttachment.objects.create(
                    purchase=purchase,
                    file=f,
                    original_name=f.name,
                    file_type=getattr(f, "content_type", ""),
                    uploaded_by=request.user,
                )
            post_purchase(purchase, request.user)
            return redirect("warehouse_stock")
    else:
        from wms.masters.models import Warehouse
        first_wh = Warehouse.objects.filter(is_active=True).order_by("name").first()
        header_form = PurchaseHeaderForm(initial={"warehouse": first_wh} if first_wh else None)
        if item_id:
            formset = PurchaseLineFormSet(initial=[{"item": item_id}])
        else:
            formset = PurchaseLineFormSet()

    return render(
        request,
        "purchasing/purchase_form.html",
        {
            "header_form": header_form,
            "formset": formset,
            "title": _("New Purchase"),
            "submit_label": _("Save & Post"),
        },
    )


@login_required
@permission_required("purchasing.change_purchaseheader", raise_exception=True)
@transaction.atomic
def purchase_edit(request, purchase_id: int):
    purchase = get_object_or_404(PurchaseHeader, pk=purchase_id)

    if request.method == "POST":
        header_form = PurchaseHeaderForm(request.POST, instance=purchase)
        formset = PurchaseEditLineFormSet(request.POST, instance=purchase)
        if header_form.is_valid() and formset.is_valid():
            unpost_purchase_inventory(purchase)
            purchase.refresh_from_db(fields=["is_posted", "posted_at"])

            purchase = header_form.save(commit=False)
            purchase.is_posted = False
            purchase.posted_at = None
            purchase.save()
            formset.instance = purchase
            _save_purchase_lines(purchase, formset)
            post_purchase(purchase, request.user)
            return redirect("purchase_detail", purchase_id=purchase.id)
    else:
        header_form = PurchaseHeaderForm(instance=purchase)
        formset = PurchaseEditLineFormSet(instance=purchase)

    return render(
        request,
        "purchasing/purchase_form.html",
        {
            "header_form": header_form,
            "formset": formset,
            "title": _("Edit Purchase"),
            "submit_label": _("Save Changes"),
        },
    )


@login_required
@permission_required("purchasing.view_purchaseheader", raise_exception=True)
def purchase_detail(request, purchase_id: int):
    purchase = get_object_or_404(PurchaseHeader, pk=purchase_id)
    if request.method == "POST":
        if not request.user.has_perm("purchasing.change_purchaseheader"):
            raise PermissionDenied
        action = request.POST.get("action")
        if action == "add_attachment":
            for f in request.FILES.getlist("attachments"):
                if Path(f.name).suffix.lower() not in _ALLOWED_ATTACHMENT_EXTS:
                    messages.warning(request, _("File type not allowed, skipped: %(name)s") % {"name": f.name})
                    continue
                PurchaseAttachment.objects.create(
                    purchase=purchase,
                    file=f,
                    original_name=f.name,
                    file_type=getattr(f, "content_type", ""),
                    uploaded_by=request.user,
                )
        elif action == "delete_attachment":
            attachment_id = request.POST.get("attachment_id")
            attachment = get_object_or_404(PurchaseAttachment, pk=attachment_id, purchase=purchase)
            attachment.delete()
        return redirect("purchase_detail", purchase_id=purchase.id)

    lines = purchase.lines.select_related("item")
    total = purchase.lines.aggregate(t=Sum("line_total"))["t"] or 0
    return render(
        request,
        "purchasing/purchase_detail.html",
        {
            "purchase": purchase,
            "lines": lines,
            "total": total,
            "attachments": purchase.attachments.order_by("-uploaded_at"),
            "can_change_purchase": request.user.has_perm("purchasing.change_purchaseheader"),
        },
    )
