import uuid
import datetime as dt
from django.core.exceptions import ValidationError
from django.db import models as djm
from django.db.models import functions as db_funcs
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from core.models.custom import mixins as core_mixins


class Project(core_mixins.TreeMixin, djm.Model):
    uuid = djm.UUIDField(default=uuid.uuid4, editable=False)
    title = djm.CharField(max_length=200)
    detail = djm.TextField(blank=True)
    workspace = djm.ForeignKey("core.Workspace", on_delete=djm.CASCADE,
                               related_name="projects")
    category = djm.ForeignKey("core.Category", on_delete=djm.CASCADE,
                              related_name="projects")
    tags = djm.ManyToManyField("core.Tag", blank=True,
                               related_name="projects")
    status = djm.ForeignKey("core.Status", on_delete=djm.CASCADE, null=True,
                            blank=True, related_name="projects")
    priority = djm.ForeignKey("core.Priority", on_delete=djm.SET_NULL,
                              null=True, blank=True, related_name="projects")
    parent = djm.ForeignKey('self', on_delete=djm.SET_NULL, null=True,
                            blank=True, related_name="children")
    is_visible = djm.BooleanField(default=True)
    estimated_start_date = djm.DateTimeField(null=True, blank=True)
    estimated_end_date = djm.DateTimeField(null=True, blank=True)
    actual_start_date = djm.DateTimeField(null=True, blank=True)
    actual_end_date = djm.DateTimeField(null=True, blank=True)
    estimated_effort = djm.PositiveSmallIntegerField(null=True, blank=True,
                                                     help_text=_("in days"))
    actual_effort = djm.PositiveSmallIntegerField(null=True, blank=True,
                                                  help_text=_("in days"))
    created_at = djm.DateTimeField(auto_now_add=True)
    updated_at = djm.DateTimeField(auto_now=True)

    @property
    def due_in(self):
        if self.estimated_end_date:
            return self.estimated_end_date - dt.datetime.now()
        return None

    def __str__(self):
        return (
            f'{self.title}'
            f' | ws: {self.workspace.name}'
            f' | cat: {self.category.name}'
        )

    def get_absolute_url(self):
        return reverse("demo:project-detail", kwargs={"uuid": self.uuid})

    def update_task_visibility(self):
        if self.tasks:
            for task in self.tasks.all():
                task.is_visible = self.is_visible
                task.save()

    def update_children_visibility(self):
        # move children to project if root parent is moved
        children = self.get_children(self)
        if children:
            for child in children:
                child.is_visible = self.is_visible
                child.save()
                child.update_children_visibility()

    def clean(self, *args, **kwargs):
        if self.category and self.category.workspace != self.workspace:
            raise ValidationError(
                "Category, status and priority should be from same workspace as self.")

        if self.status and self.status.workspace != self.workspace:
            raise ValidationError(
                "Category, status and priority should be from same workspace as self.")

        if self.priority and self.priority.workspace != self.workspace:
            raise ValidationError(
                "Category, status and priority should be from same workspace as self.")

        if self.parent:
            if self.is_visible != self.parent.is_visible:
                raise ValidationError(
                    "Visibility should be same as of parent's."
                )
        return super().clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.pk:
            self.update_task_visibility()
        if self.pk and not self.parent:
            if self.children.all().exists():
                self.update_children_visibility()

    class Meta:
        constraints = [
            djm.UniqueConstraint(
                db_funcs.Lower("title"), "workspace", "category",
                name="unique_lower_project_title_category_workspace"
            ),
        ]
