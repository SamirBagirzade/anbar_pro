from rest_framework import serializers
from .models import Vendor, Warehouse, OutgoingLocation, Item, VendorItem


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = "__all__"


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = "__all__"


class OutgoingLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutgoingLocation
        fields = "__all__"


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = "__all__"


class VendorItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorItem
        fields = "__all__"
