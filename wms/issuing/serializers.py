from rest_framework import serializers
from .models import IssueHeader, IssueLine


class IssueLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueLine
        fields = ["id", "item", "qty"]


class IssueSerializer(serializers.ModelSerializer):
    lines = IssueLineSerializer(many=True)

    class Meta:
        model = IssueHeader
        fields = [
            "id",
            "warehouse",
            "outgoing_location",
            "issue_date",
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
        issue = IssueHeader.objects.create(**validated_data)
        for line in lines_data:
            IssueLine.objects.create(header=issue, **line)
        return issue
