from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions
from .models import Vendor, Warehouse, OutgoingLocation, Item
from .serializers import VendorSerializer, WarehouseSerializer, OutgoingLocationSerializer, ItemSerializer


class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [DjangoModelPermissions]


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [DjangoModelPermissions]


class OutgoingLocationViewSet(viewsets.ModelViewSet):
    queryset = OutgoingLocation.objects.all()
    serializer_class = OutgoingLocationSerializer
    permission_classes = [DjangoModelPermissions]


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [DjangoModelPermissions]
