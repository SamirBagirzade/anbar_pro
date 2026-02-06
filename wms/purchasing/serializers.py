from rest_framework import serializers
from .models import PurchaseHeader, PurchaseLine, PurchaseAttachment


class PurchaseLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseLine
        fields = ["id", "item", "qty", "unit_price", "discount", "tax_rate", "line_total"]


class PurchaseAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseAttachment
        fields = ["id", "file", "original_name", "file_type", "uploaded_by", "uploaded_at"]
        read_only_fields = ["uploaded_by", "uploaded_at"]


class PurchaseSerializer(serializers.ModelSerializer):
    lines = PurchaseLineSerializer(many=True)

    class Meta:
        model = PurchaseHeader
        fields = [
            "id",
            "vendor",
            "warehouse",
            "invoice_no",
            "invoice_date",
            "currency",
            "notes",
            "created_by",
            "created_at",
            "updated_at",
            "is_posted",
            "posted_at",
            "lines",
        ]
        read_only_fields = ["created_by", "created_at", "updated_at", "posted_at"]

    def create(self, validated_data):
        lines_data = validated_data.pop("lines")
        purchase = PurchaseHeader.objects.create(**validated_data)
        for line in lines_data:
            PurchaseLine.objects.create(purchase=purchase, **line)
        return purchase
