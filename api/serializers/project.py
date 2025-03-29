from rest_framework import serializers

from core import models as core_models
from . import custom_classes


class ProjectSerializer(custom_classes.CustomBaseSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True, read_only=False, queryset=core_models.Tag.objects.all()
    )

    class Meta:
        model = core_models.Project
        fields = [
            "id", "uuid", "title", "detail", "workspace", "category",
            "tags", "status", "priority", "parent", "is_visible",
            "estimated_start_date", "estimated_end_date",
            "actual_start_date", "actual_end_date",
            "estimated_effort", "actual_effort",
            "created_at", "updated_at",
        ]
