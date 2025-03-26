from django.contrib.auth import get_user_model
from django.test import TestCase

from core import models as core_models


class CustomTestCaseSetup(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()

    @classmethod
    def create_user(cls, username='user-1', password='testpass123'):
        """Create and return user."""
        return get_user_model().objects.create_user(username=username, password=password)

    @classmethod
    def db_create_workspaces(cls, user, multiple=True):
        cls.workspace_1 = core_models.Workspace.objects.create(
            name="workspace 1",
            created_by=user.id,
            is_default=True,
        )
        if multiple:
            cls.workspace_2 = core_models.Workspace.objects.create(
                name="Workspace 2",
                created_by=user.id,
                is_default=False,
            )

    @classmethod
    def db_create_tags(cls, user, workspace, multiple=True):
        tag_1_attr_name = f'ws_{workspace.pk}_tag_1'
        setattr(cls, tag_1_attr_name,
                core_models.Tag.objects.create(
                    name="tag 1",
                    workspace=workspace,
                ))
        if multiple:
            tag_2_attr_name = f'ws_{workspace.pk}_tag_2'
            setattr(cls, tag_2_attr_name,
                    core_models.Tag.objects.create(
                        name="tag 2",
                        workspace=workspace,
                    ))

    @classmethod
    def db_create_priorities(cls, user, workspace, multiple=True):
        priority_1_attr_name = f'ws_{workspace.pk}_priority_1'
        setattr(cls, priority_1_attr_name,
                core_models.Priority.objects.create(
                    name="priority 1",
                    workspace=workspace,
                ))
        if multiple:
            priority_2_attr_name = f'ws_{workspace.pk}_priority_2'
            setattr(cls, priority_2_attr_name,
                    core_models.Priority.objects.create(
                        name="priority 2",
                        workspace=workspace,
                    ))

    @classmethod
    def db_create_statuses(cls, user, workspace, multiple=True):
        status_1_attr_name = f'ws_{workspace.pk}_status_1'
        setattr(cls, status_1_attr_name,
                core_models.Status.objects.create(
                    name="status 1",
                    workspace=workspace,
                ))
        if multiple:
            status_2_attr_name = f'ws_{workspace.pk}_status_2'
            setattr(cls, status_2_attr_name,
                    core_models.Status.objects.create(
                        name="status 2",
                        workspace=workspace,
                    ))

    @classmethod
    def db_create_categories(cls, user, workspace, multiple=True):
        category_1_attr_name = f'ws_{workspace.pk}_category_1'
        setattr(cls, category_1_attr_name,
                core_models.Category.objects.create(
                    name="category 1",
                    workspace=workspace,
                ))
        if multiple:
            category_2_attr_name = f'ws_{workspace.pk}_category_2'
            setattr(cls, category_2_attr_name,
                    core_models.Category.objects.create(
                        name="category 2",
                        workspace=workspace,
                    ))

    @classmethod
    def db_create_projects(cls, user, category, multiple=True):
        project_1_attr_name = f'cat_{category.pk}_project_1'
        setattr(cls, project_1_attr_name,
                core_models.Project.objects.create(
                    title="project 1",
                    workspace=category.workspace,
                    category=category,
                ))
        if multiple:
            project_2_attr_name = f'cat_{category.pk}_project_2'
            setattr(cls, project_2_attr_name,
                    core_models.Project.objects.create(
                        title="project 2",
                        workspace=category.workspace,
                        category=category,
                    ))

    @classmethod
    def db_create_tasks(cls, user, category, project=None, multiple=True):
        if project:
            task_1_attr_name = f'cat_{category.pk}_pr_{project.pk}_task_1'
        else:
            task_1_attr_name = f'cat_{category.pk}_task_1'
        setattr(cls, task_1_attr_name,
                core_models.Task.objects.create(
                    title="task 1",
                    workspace=category.workspace,
                    category=category,
                    project=project,
                ))
        if multiple:
            task_2_attr_name = f'cat_{category.pk}_task_2'
            setattr(cls, task_2_attr_name,
                    core_models.Task.objects.create(
                        title="task 2",
                        workspace=category.workspace,
                        category=category,
                        project=project,
                    ))

    @staticmethod
    def get_workspace_query(pk_seq=None):
        if pk_seq:
            return core_models.Workspace.objects.filter(pk__in=pk_seq)
        return core_models.Workspace.objects.all()

    @staticmethod
    def get_tag_query(pk_seq=None, ws_pk_seq=None):
        qry = core_models.Tag.objects.all()
        if pk_seq:
            qry = qry.filter(pk__in=pk_seq)
        if ws_pk_seq:
            qry = qry.filter(workspace__pk__in=ws_pk_seq)
        return qry

    @staticmethod
    def get_priority_query(pk_seq=None, ws_pk_seq=None):
        qry = core_models.Priority.objects.all()
        if pk_seq:
            qry = qry.filter(pk__in=pk_seq)
        if ws_pk_seq:
            qry = qry.filter(workspace__pk__in=ws_pk_seq)
        return qry

    @staticmethod
    def get_status_query(pk_seq=None, ws_pk_seq=None):
        qry = core_models.Status.objects.all()
        if pk_seq:
            qry = qry.filter(pk__in=pk_seq)
        if ws_pk_seq:
            qry = qry.filter(workspace__pk__in=ws_pk_seq)
        return qry

    @staticmethod
    def get_category_query(pk_seq=None, ws_pk_seq=None):
        qry = core_models.Category.objects.all()
        if pk_seq:
            qry = qry.filter(pk__in=pk_seq)
        if ws_pk_seq:
            qry = qry.filter(workspace__pk__in=ws_pk_seq)
        return qry

    @staticmethod
    def get_project_query(pk_seq=None, cat_pk_seq=None):
        qry = core_models.Project.objects.all()
        if pk_seq:
            qry = qry.filter(pk__in=pk_seq)
        if cat_pk_seq:
            qry = qry.filter(category__pk__in=cat_pk_seq)
        return qry

    @staticmethod
    def get_task_query(pk_seq=None, cat_pk_seq=None, pr_pk_seq=None):
        qry = core_models.Task.objects.all()
        if pk_seq:
            qry = qry.filter(pk__in=pk_seq)
        if cat_pk_seq:
            qry = qry.filter(category__pk__in=cat_pk_seq)
        if pr_pk_seq:
            qry = qry.filter(project__pk__in=pr_pk_seq)
        return qry
