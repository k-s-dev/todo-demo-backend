from core import models as core_models
from . import custom_classes


class CategorySerializer(custom_classes.CustomBaseSerializer):
    class Meta:
        model = core_models.Category
        fields = [
            "id", "name", "description", "workspace", "parent",
            "created_at", "updated_at",
        ]
