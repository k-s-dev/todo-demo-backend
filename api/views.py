from rest_framework import permissions

from api.serializers import workspace as workspace_serializers
from api.serializers import category as category_serializers
from api.serializers import project as project_serializers
from api.serializers import task as task_serializers
from . import permissions as api_permissions
from api.custom import views as custom_views


class WorkspaceViewSet(custom_views.CustomBaseModelViewSet):
    serializer_class = workspace_serializers.WorkspaceSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        api_permissions.IsAdmin,
    ]


class CategoryViewSet(custom_views.CustomBaseModelViewSetUser):
    serializer_class = category_serializers.CategorySerializer
    permission_classes = [
        permissions.IsAuthenticated,
        api_permissions.IsAdmin,
    ]


class ProjectViewSet(custom_views.CustomBaseModelViewSetUser):
    serializer_class = project_serializers.ProjectSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        api_permissions.IsAdmin,
    ]


class TaskViewSet(custom_views.CustomBaseModelViewSetUser):
    serializer_class = task_serializers.TaskSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        api_permissions.IsAdmin,
    ]


class TagViewSet(custom_views.CustomBaseModelViewSetUser):
    serializer_class = workspace_serializers.TagSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        api_permissions.IsAdmin,
    ]


class PriorityViewSet(custom_views.CustomBaseModelViewSetUser):
    serializer_class = workspace_serializers.PrioritySerializer
    permission_classes = [
        permissions.IsAuthenticated,
        api_permissions.IsAdmin,
    ]


class StatusViewSet(custom_views.CustomBaseModelViewSetUser):
    serializer_class = workspace_serializers.StatusSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        api_permissions.IsAdmin,
    ]
