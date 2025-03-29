from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Custom permission to allow only owner or admin to create, view or edit objects.
    """
    def has_object_permission(self, request, view, obj):
        return request.user.is_superuser
