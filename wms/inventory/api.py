from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions
from .models import StockBalance, StockMovement, TransferHeader, AdjustmentHeader
from .serializers import (
    StockBalanceSerializer,
    StockMovementSerializer,
    TransferSerializer,
    AdjustmentSerializer,
)


class StockBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockBalance.objects.all()
    serializer_class = StockBalanceSerializer
    permission_classes = [DjangoModelPermissions]


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockMovement.objects.all().order_by("-created_at")
    serializer_class = StockMovementSerializer
    permission_classes = [DjangoModelPermissions]


class TransferViewSet(viewsets.ModelViewSet):
    queryset = TransferHeader.objects.all().order_by("-created_at")
    serializer_class = TransferSerializer
    permission_classes = [DjangoModelPermissions]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AdjustmentViewSet(viewsets.ModelViewSet):
    queryset = AdjustmentHeader.objects.all().order_by("-created_at")
    serializer_class = AdjustmentSerializer
    permission_classes = [DjangoModelPermissions]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
