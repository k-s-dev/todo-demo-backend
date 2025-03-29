from core import models as core_models
from . import custom_classes


class WorkspaceSerializer(custom_classes.CustomBaseSerializer):
    class Meta:
        model = core_models.Workspace
        fields = [
            "id", "name", "description", "is_default",
            "created_by", "created_at", "updated_at",
        ]


class TagSerializer(custom_classes.CustomBaseSerializer):
    class Meta:
        model = core_models.Tag
        fields = [
            "id", "name", "workspace",
            "created_at", "updated_at"
        ]


class PrioritySerializer(custom_classes.CustomBaseSerializer):
    class Meta:
        model = core_models.Priority
        fields = [
            "id", "name", "description", "order", "workspace",
            "created_at", "updated_at"
        ]


class StatusSerializer(custom_classes.CustomBaseSerializer):
    class Meta:
        model = core_models.Status
        fields = [
            "id", "name", "description", "order", "workspace",
            "created_at", "updated_at",
        ]
