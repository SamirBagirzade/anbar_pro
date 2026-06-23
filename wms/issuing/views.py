from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from datetime import datetime
from pathlib import Path
from .forms import IssueHeaderForm, IssueLineFormSet, IssueEditLineFormSet, build_issue_create_formset

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
from wms.inventory.services import post_issue, delete_issue_with_inventory, unpost_issue_inventory
from wms.purchasing.models import PurchaseHeader
from .models import IssueAttachment, IssueHeader, IssueLine


def _can_delete_issue(user):
    return user.is_superuser or user.has_perm("issuing.delete_issueheader")


def _save_issue_lines(issue, formset):
    issue.lines.all().delete()
    for form in formset:
        if not form.cleaned_data or form.cleaned_data.get("DELETE"):
            continue
        item = form.cleaned_data.get("item")
        qty = form.cleaned_data.get("qty")
        if not item or qty is None:
            continue
        IssueLine.objects.create(header=issue, item=item, qty=qty)


@login_required
@permission_required("issuing.view_issueheader", raise_exception=True)
def issue_list(request):
    if request.method == "POST":
        if not _can_delete_issue(request.user):
            raise PermissionDenied
        issue_id = request.POST.get("issue_id")
        issue = get_object_or_404(IssueHeader, pk=issue_id)
        delete_issue_with_inventory(issue)
        return redirect("issue_list")

    from wms.masters.models import Warehouse, OutgoingLocation
    warehouse_id = request.GET.get("warehouse", "").strip()
    location_id = request.GET.get("outgoing_location", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    date_from_parsed = _parse_date(date_from)
    date_to_parsed = _parse_date(date_to)

    issues = (
        IssueHeader.objects.select_related("warehouse", "outgoing_location")
        .annotate(line_count=Count("lines", distinct=True), total_qty=Sum("lines__qty"))
        .order_by("-issue_date", "-id")
    )
    if warehouse_id:
        issues = issues.filter(warehouse_id=warehouse_id)
    if location_id:
        issues = issues.filter(outgoing_location_id=location_id)
    if date_from_parsed:
        issues = issues.filter(issue_date__gte=date_from_parsed)
    if date_to_parsed:
        issues = issues.filter(issue_date__lte=date_to_parsed)

    return render(
        request,
        "issuing/issue_list.html",
        {
            "issues": issues,
            "can_delete_issue": _can_delete_issue(request.user),
            "can_change_issue": request.user.has_perm("issuing.change_issueheader"),
            "warehouses": Warehouse.objects.filter(is_active=True).order_by("name"),
            "outgoing_locations": OutgoingLocation.objects.filter(is_active=True).order_by("name"),
            "selected_warehouse_id": warehouse_id,
            "selected_location_id": location_id,
            "date_from": date_from,
            "date_to": date_to,
        },
    )


@login_required
@permission_required("issuing.add_issueheader", raise_exception=True)
@transaction.atomic
def issue_create(request):
    CreateFormSet = IssueLineFormSet
    source_purchase = None
    if request.method == "POST":
        source_purchase_id = (request.POST.get("source_purchase_id") or "").strip()
        if source_purchase_id.isdigit():
            source_purchase = PurchaseHeader.objects.filter(pk=int(source_purchase_id)).first()
        warehouse_id = request.POST.get("warehouse") or None
        header_form = IssueHeaderForm(request.POST)
        formset = CreateFormSet(request.POST, form_kwargs={"warehouse_id": warehouse_id})
        if header_form.is_valid() and formset.is_valid():
            issue = header_form.save(commit=False)
            issue.created_by = request.user
            issue.source_purchase = source_purchase
            issue.save()
            formset.instance = issue
            _save_issue_lines(issue, formset)
            for f in request.FILES.getlist("attachments"):
                if Path(f.name).suffix.lower() not in _ALLOWED_ATTACHMENT_EXTS:
                    messages.warning(request, _("File type not allowed, skipped: %(name)s") % {"name": f.name})
                    continue
                IssueAttachment.objects.create(
                    header=issue,
                    file=f,
                    original_name=f.name,
                    file_type=getattr(f, "content_type", ""),
                    uploaded_by=request.user,
                )
            post_issue(issue, request.user)
            return redirect("warehouse_stock")
    else:
        from wms.masters.models import Warehouse
        purchase_id = (request.GET.get("purchase") or "").strip()
        if purchase_id.isdigit():
            source_purchase = (
                PurchaseHeader.objects.filter(pk=int(purchase_id)).prefetch_related("lines").first()
            )

        first_wh = Warehouse.objects.filter(is_active=True).order_by("name").first()
        initial_header = {"warehouse": first_wh} if first_wh else {}
        warehouse_id = None
        if source_purchase:
            initial_header["warehouse"] = source_purchase.warehouse_id
            warehouse_id = source_purchase.warehouse_id
        elif first_wh:
            warehouse_id = first_wh.id
        header_form = IssueHeaderForm(initial=initial_header)

        if source_purchase:
            lines_initial = [{"item": line.item_id, "qty": line.qty} for line in source_purchase.lines.all()]
            CreateFormSet = build_issue_create_formset(extra=max(3, len(lines_initial)))
            formset = CreateFormSet(
                initial=lines_initial if lines_initial else None,
                form_kwargs={"warehouse_id": warehouse_id},
            )
        else:
            formset = CreateFormSet(form_kwargs={"warehouse_id": warehouse_id})

    return render(
        request,
        "issuing/issue_form.html",
        {
            "header_form": header_form,
            "formset": formset,
            "source_purchase": source_purchase,
            "title": _("New Issue"),
            "submit_label": _("Save & Post"),
        },
    )


@login_required
@permission_required("issuing.change_issueheader", raise_exception=True)
@transaction.atomic
def issue_edit(request, issue_id: int):
    issue = get_object_or_404(IssueHeader, pk=issue_id)

    if request.method == "POST":
        warehouse_id = request.POST.get("warehouse") or issue.warehouse_id
        header_form = IssueHeaderForm(request.POST, instance=issue)
        formset = IssueEditLineFormSet(request.POST, instance=issue, form_kwargs={"warehouse_id": warehouse_id})
        if header_form.is_valid() and formset.is_valid():
            unpost_issue_inventory(issue)
            issue.refresh_from_db(fields=["is_posted", "posted_at"])

            issue = header_form.save(commit=False)
            issue.is_posted = False
            issue.posted_at = None
            issue.save()
            formset.instance = issue
            _save_issue_lines(issue, formset)
            post_issue(issue, request.user)
            return redirect("issue_detail", issue_id=issue.id)
    else:
        header_form = IssueHeaderForm(instance=issue)
        formset = IssueEditLineFormSet(instance=issue, form_kwargs={"warehouse_id": issue.warehouse_id})

    return render(
        request,
        "issuing/issue_form.html",
        {
            "header_form": header_form,
            "formset": formset,
            "title": _("Edit Issue"),
            "submit_label": _("Save Changes"),
        },
    )


@login_required
@permission_required("issuing.view_issueheader", raise_exception=True)
def issue_detail(request, issue_id: int):
    issue = get_object_or_404(IssueHeader, pk=issue_id)
    if request.method == "POST":
        if not request.user.has_perm("issuing.change_issueheader"):
            raise PermissionDenied
        action = request.POST.get("action")
        if action == "add_attachment":
            for f in request.FILES.getlist("attachments"):
                if Path(f.name).suffix.lower() not in _ALLOWED_ATTACHMENT_EXTS:
                    messages.warning(request, _("File type not allowed, skipped: %(name)s") % {"name": f.name})
                    continue
                IssueAttachment.objects.create(
                    header=issue,
                    file=f,
                    original_name=f.name,
                    file_type=getattr(f, "content_type", ""),
                    uploaded_by=request.user,
                )
        elif action == "delete_attachment":
            attachment_id = request.POST.get("attachment_id")
            attachment = get_object_or_404(IssueAttachment, pk=attachment_id, header=issue)
            attachment.delete()
        return redirect("issue_detail", issue_id=issue.id)

    lines = issue.lines.select_related("item")
    total_qty = issue.lines.aggregate(t=Sum("qty"))["t"] or 0
    return render(
        request,
        "issuing/issue_detail.html",
        {
            "issue": issue,
            "lines": lines,
            "total_qty": total_qty,
            "attachments": issue.attachments.order_by("-uploaded_at"),
            "can_change_issue": request.user.has_perm("issuing.change_issueheader"),
        },
    )
