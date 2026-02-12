from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum
from django.db import transaction
from .forms import IssueHeaderForm, IssueLineFormSet
from wms.inventory.services import post_issue
from .models import IssueAttachment, IssueHeader


@login_required
@permission_required("issuing.view_issueheader", raise_exception=True)
def issue_list(request):
    issues = (
        IssueHeader.objects.select_related("warehouse", "outgoing_location")
        .annotate(line_count=Count("lines", distinct=True), total_qty=Sum("lines__qty"))
        .order_by("-issue_date", "-id")
    )
    return render(request, "issuing/issue_list.html", {"issues": issues})


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
            formset.save()
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
        },
    )
