from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from .forms import IssueHeaderForm, IssueLineFormSet, IssueEditLineFormSet
from wms.inventory.services import post_issue, delete_issue_with_inventory, unpost_issue_inventory
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

    issues = (
        IssueHeader.objects.select_related("warehouse", "outgoing_location")
        .annotate(line_count=Count("lines", distinct=True), total_qty=Sum("lines__qty"))
        .order_by("-issue_date", "-id")
    )
    return render(
        request,
        "issuing/issue_list.html",
        {
            "issues": issues,
            "can_delete_issue": _can_delete_issue(request.user),
            "can_change_issue": request.user.has_perm("issuing.change_issueheader"),
        },
    )


@login_required
@permission_required("issuing.add_issueheader", raise_exception=True)
@transaction.atomic
def issue_create(request):
    if request.method == "POST":
        header_form = IssueHeaderForm(request.POST)
        formset = IssueLineFormSet(request.POST)
        if header_form.is_valid() and formset.is_valid():
            issue = header_form.save(commit=False)
            issue.created_by = request.user
            issue.save()
            formset.instance = issue
            _save_issue_lines(issue, formset)
            for f in request.FILES.getlist("attachments"):
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
        first_wh = Warehouse.objects.filter(is_active=True).order_by("name").first()
        header_form = IssueHeaderForm(initial={"warehouse": first_wh} if first_wh else None)
        formset = IssueLineFormSet()

    return render(
        request,
        "issuing/issue_form.html",
        {
            "header_form": header_form,
            "formset": formset,
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
        header_form = IssueHeaderForm(request.POST, instance=issue)
        formset = IssueEditLineFormSet(request.POST, instance=issue)
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
        formset = IssueEditLineFormSet(instance=issue)

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

    return render(
        request,
        "issuing/issue_detail.html",
        {
            "issue": issue,
            "lines": issue.lines.select_related("item"),
            "attachments": issue.attachments.order_by("-uploaded_at"),
            "can_change_issue": request.user.has_perm("issuing.change_issueheader"),
        },
    )
