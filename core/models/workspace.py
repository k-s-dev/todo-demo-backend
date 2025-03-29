from django.core.exceptions import ValidationError
from django.db import models as djm
from django.db.models import Q, functions as db_funcs
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from core.models.custom import mixins as core_mixins


class Workspace(djm.Model):
    name = djm.CharField(_("name"), max_length=200, default="default")
    description = djm.TextField(blank=True)
    is_default = djm.BooleanField(default=False)
    created_at = djm.DateTimeField(auto_now_add=True)
    updated_at = djm.DateTimeField(auto_now=True)
    created_by = djm.CharField(max_length=300)

    def __str__(self):
        return f'{self.name}-{self.created_by}'

    def get_absolute_url(self):
        return reverse('demo:workspace-detail', args=[self.pk])

    def update_default_workspace(self):
        # remove existing default if updating default flag to true in some other
        # workspace
        default_workspaces_query = Workspace.objects.filter(
            Q(is_default=True)
            & Q(created_by=self.created_by)
            & ~Q(pk=self.pk)
        )
        if default_workspaces_query.exists():
            other_default_workspace = default_workspaces_query[0]
        else:
            other_default_workspace = None
        if self.is_default and other_default_workspace:
            other_default_workspace.is_default = False
            other_default_workspace.save()
        # when creating, assign default if no other default exists
        if not self.pk and not Workspace.objects.filter(
            Q(is_default=True)
            & Q(created_by=self.created_by)
        ).exists():
            self.is_default = True

    def clean(self, *args, **kwargs):
        # raise error if there is no default workspace
        if self.pk:
            default_workspaces_query = Workspace.objects.filter(
                Q(is_default=True)
                & Q(created_by=self.created_by)
                & ~Q(pk=self.pk)
            )
            if not self.is_default and not default_workspaces_query.exists():
                raise ValidationError(
                    "There has to be at-least one default workspace."
                )
        return super().clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.update_default_workspace()
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            djm.UniqueConstraint(
                db_funcs.Lower("name"), "created_by",
                name="unique_lower_workspace_owner_name",
            ),
        ]


class Category(core_mixins.TreeMixin, djm.Model):
    """
    Workspace categories for segregating projects and tasks.
    """
    name = djm.CharField(max_length=200)
    description = djm.CharField(max_length=500, null=True, blank=True)
    workspace = djm.ForeignKey("core.Workspace", on_delete=djm.CASCADE,
                               related_name="categories")
    parent = djm.ForeignKey('self', on_delete=djm.SET_NULL, null=True,
                            blank=True, related_name="children")
    created_at = djm.DateTimeField(auto_now_add=True)
    updated_at = djm.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        category, parent = self, self.parent
        result = [category.name]
        while parent:
            result.append(parent.name)
            category = parent
            parent = category.parent
        return ' --> '.join(list(reversed(result)))

    def get_absolute_url(self):
        return reverse('demo:category-detail', args=[str(self.pk)])

    class Meta:
        verbose_name = _("workspace category")
        verbose_name_plural = _("workspace categories")
        constraints = [
            djm.UniqueConstraint(
                db_funcs.Lower("name"), "workspace",
                name="unique_lower_category_name_workspace",
            ),
        ]


class Tag(djm.Model):
    name = djm.CharField(_("name"), max_length=200)
    workspace = djm.ForeignKey(
        "core.Workspace", on_delete=djm.CASCADE, related_name="tags")
    created_at = djm.DateTimeField(auto_now_add=True)
    updated_at = djm.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("workspace tag")
        constraints = [
            djm.UniqueConstraint(db_funcs.Lower("name"), "workspace",
                                 name="unique_lower_tag_name_workspace"),
        ]


class Priority(djm.Model):
    name = djm.CharField(_("name"), max_length=200)
    description = djm.CharField(max_length=500, null=True, blank=True)
    order = djm.SmallIntegerField(default=0, null=True)
    workspace = djm.ForeignKey("core.Workspace", on_delete=djm.CASCADE,
                               related_name="priorities")
    created_at = djm.DateTimeField(auto_now_add=True)
    updated_at = djm.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Workspace priority")
        verbose_name_plural = _("Workspace priorities")
        constraints = [
            djm.UniqueConstraint(db_funcs.Lower("name"), "workspace",
                                 name="unique_lower_priority_name_workspace"),
        ]


class Status(djm.Model):
    name = djm.CharField(_("name"), max_length=200)
    description = djm.CharField(max_length=500, null=True, blank=True)
    order = djm.SmallIntegerField(default=0, null=True)
    workspace = djm.ForeignKey("core.Workspace", on_delete=djm.CASCADE,
                               related_name="statuses")
    created_at = djm.DateTimeField(auto_now_add=True)
    updated_at = djm.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Workspace status")
        verbose_name_plural = _("Workspace statuses")
        constraints = [
            djm.UniqueConstraint(db_funcs.Lower("name"), "workspace",
                                 name="unique_lower_status_name_workspace"),
        ]
