from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions
from .models import IssueHeader
from .serializers import IssueSerializer


class IssueViewSet(viewsets.ModelViewSet):
    queryset = IssueHeader.objects.all().order_by("-created_at")
    serializer_class = IssueSerializer
    permission_classes = [DjangoModelPermissions]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
