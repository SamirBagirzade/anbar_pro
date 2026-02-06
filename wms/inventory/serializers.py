from rest_framework import serializers
from .models import StockBalance, StockMovement, TransferHeader, TransferLine, AdjustmentHeader, AdjustmentLine


class StockBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockBalance
        fields = "__all__"


class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = "__all__"
        read_only_fields = ["created_by", "created_at"]


class TransferLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransferLine
        fields = ["id", "item", "qty"]


class TransferSerializer(serializers.ModelSerializer):
    lines = TransferLineSerializer(many=True)

    class Meta:
        model = TransferHeader
        fields = [
            "id",
            "from_warehouse",
            "to_warehouse",
            "date",
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
        transfer = TransferHeader.objects.create(**validated_data)
        for line in lines_data:
            TransferLine.objects.create(header=transfer, **line)
        return transfer


class AdjustmentLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdjustmentLine
        fields = ["id", "item", "qty_delta"]


class AdjustmentSerializer(serializers.ModelSerializer):
    lines = AdjustmentLineSerializer(many=True)

    class Meta:
        model = AdjustmentHeader
        fields = [
            "id",
            "warehouse",
            "date",
            "reason",
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
        adjustment = AdjustmentHeader.objects.create(**validated_data)
        for line in lines_data:
            AdjustmentLine.objects.create(header=adjustment, **line)
        return adjustment
