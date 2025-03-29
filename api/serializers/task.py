from core import models as core_models
from . import custom_classes


class TaskSerializer(custom_classes.CustomBaseSerializer):
    class Meta:
        model = core_models.Task
        fields = [
            "id", "uuid", "title", "detail",
            "workspace", "category", "project",
            "tags", "status", "priority", "parent", "is_visible",
            "estimated_start_date", "estimated_end_date",
            "actual_start_date", "actual_end_date",
            "estimated_effort", "actual_effort",
            "created_at", "updated_at",
        ]
