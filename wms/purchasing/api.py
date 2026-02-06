from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions
from .models import PurchaseHeader
from .serializers import PurchaseSerializer


class PurchaseViewSet(viewsets.ModelViewSet):
    queryset = PurchaseHeader.objects.all().order_by("-created_at")
    serializer_class = PurchaseSerializer
    permission_classes = [DjangoModelPermissions]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
