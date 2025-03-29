from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework.exceptions import status
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.request import Request
from rest_framework.parsers import JSONParser

from core import models as core_models
from api import serializers as api_serializers


class CustomTestCaseSetup(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.api_factory = APIRequestFactory()
        temp_get_request = cls.api_factory.get(
            '/', content_type='application/json')
        cls.request_tmp = Request(temp_get_request, parsers=[JSONParser()])

    @classmethod
    def create_user(cls, username='user-1', password='testpass123'):
        """Create and return user."""
        return get_user_model().objects.create_user(
            username=username, password=password, is_superuser=True,)


class TaskApiMinimalSetupClass(CustomTestCaseSetup):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = cls.create_user()
        cls.view_name_list = "api:user-task-list"
        cls.view_name_detail = "api:user-task-detail"

    def setUp(self):
        super().setUp()
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_authenticate(self.user)

    @staticmethod
    def get_workspace_query(pk_seq=None):
        if pk_seq:
            return core_models.Workspace.objects.filter(pk__in=pk_seq)
        return core_models.Workspace.objects.all()

    @staticmethod
    def get_category_query(pk_seq=None, user_id_seq=None):
        qry = core_models.Category.objects.all()
        if pk_seq:
            qry = qry.filter(pk__in=pk_seq)
        if user_id_seq:
            qry = qry.filter(workspace__created_by__in=user_id_seq)
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
    def get_task_query(pk_seq=None, user_id_seq=None, pr_pk_seq=None):
        qry = core_models.Task.objects.all()
        if pk_seq:
            qry = qry.filter(pk__in=pk_seq)
        if user_id_seq:
            qry = qry.filter(category__workspace__created_by__in=user_id_seq)
        if pr_pk_seq:
            qry = qry.filter(project__pk__in=pr_pk_seq)
        return qry

    @classmethod
    def db_create_workspaces(cls, user, multiple=True):
        cls.workspace_1 = core_models.Workspace.objects.create(
            name="default",
            created_by=user.id,
            is_default=True,
        )
        if multiple:
            cls.workspace_2 = core_models.Workspace.objects.create(
                name="ws 2",
                created_by=user.id,
                is_default=False,
            )

    @classmethod
    def db_create_categories(cls, user, workspace, multiple=True):
        category_1_attr_name = f'ws_{workspace.pk}_cat_1'
        setattr(cls, category_1_attr_name,
                core_models.Category.objects.create(
                    name="category 1",
                    workspace=workspace,
                ))
        if multiple:
            category_2_attr_name = f'ws_{workspace.pk}_cat_2'
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

    @classmethod
    def get_task_serializers(cls, pk_seq=None, user_id_seq=None, pr_pk_seq=None):
        task_query = cls.get_task_query(
            pk_seq=pk_seq, user_id_seq=user_id_seq, pr_pk_seq=pr_pk_seq).order_by("id")
        return api_serializers.TaskSerializer(
            task_query, many=True, context={"request": cls.request_tmp},
        )


class TaskApiFullSetupTestClass(TaskApiMinimalSetupClass):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.db_create_workspaces(cls.user)
        for workspace in cls.get_workspace_query():
            cls.db_create_categories(cls.user, workspace)
        for category in cls.get_category_query():
            cls.db_create_projects(cls.user, category)
            cls.db_create_tasks(cls.user, category)
        for project in cls.get_project_query():
            cls.db_create_tasks(cls.user, project.category, project)

    def setUp(self):
        super().setUp()


class TaskApiAuthAndCrudTests(TaskApiFullSetupTestClass):
    """Test basic auth and CRUD operations on task view api."""

    def test_auth_required(self):
        self.client.force_authenticate(None)
        response = self.client.get(reverse(
            self.view_name_list,
            kwargs={
                "user_id": self.cat_1_task_1.category.workspace.pk,
            }))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_task_get(self):
        """Test task get."""
        response = self.client.get(reverse(
            self.view_name_list,
            kwargs={
                "user_id": self.cat_1_task_1.category.workspace.created_by,
            }))
        response_1 = self.client.get(reverse(
            self.view_name_detail,
            kwargs={
                "user_id": self.cat_1_task_1.category.workspace.created_by,
                "pk": self.cat_1_task_1.pk,
            }))
        task_1_serializer = self.get_task_serializers(
            pk_seq=[self.cat_1_task_1.pk])
        cat_1_serializers = self.get_task_serializers(
            user_id_seq=[self.cat_1_task_1.category.workspace.created_by])

        assert response.status_code == status.HTTP_200_OK
        for i in range(len(cat_1_serializers.data)):
            assert response.data[i]["title"] == cat_1_serializers.data[i]["title"]
        assert response_1.data == task_1_serializer.data[0]

    def test_task_create_post(self):
        """
        Test task create post.
        """
        data = {
            "title": "task tmp",
            "workspace": self.ws_1_cat_1.workspace.pk,
            "category": self.ws_1_cat_1.pk,
            "parent": "",
        }
        url = reverse(self.view_name_list,
                      kwargs={
                          "user_id": self.cat_1_task_1.category.workspace.created_by,
                      })
        response = self.client.post(url, data)
        retrieved_data = core_models.Task.objects.filter(
            title="task tmp")
        assert response.status_code == status.HTTP_201_CREATED
        assert retrieved_data.exists()

    def test_task_update_patch(self):
        """Test task update using patch."""
        data = {
            "title": "edit 1",
        }
        url = reverse(self.view_name_detail,
                      kwargs={
                          "user_id": self.cat_1_task_1.category.workspace.created_by,
                          "pk": self.cat_1_task_1.pk,
                      })
        response = self.client.patch(url, data)
        self.cat_1_task_1.refresh_from_db()
        task_1_serializer = self.get_task_serializers(
            pk_seq=[self.cat_1_task_1.pk])
        assert response.status_code == status.HTTP_200_OK
        assert response.data == task_1_serializer.data[0]

    def test_task_update_put(self):
        """Test task update using put."""
        data = {
            "title": "task tmp",
            "workspace": self.ws_1_cat_1.workspace.pk,
            "category": self.ws_1_cat_1.pk,
            "parent": "",
        }
        url = reverse(self.view_name_detail,
                      kwargs={
                          "user_id": self.cat_1_task_1.category.workspace.created_by,
                          "pk": self.cat_1_task_1.pk,
                      })
        response = self.client.put(url, data)
        self.cat_1_task_1.refresh_from_db()
        task_1_serializer = self.get_task_serializers(
            pk_seq=[self.cat_1_task_1.pk])
        assert response.status_code == status.HTTP_200_OK
        assert response.data == task_1_serializer.data[0]

    def test_task_delete(self):
        """Test task delete."""
        url = reverse(self.view_name_detail,
                      kwargs={
                          "user_id": self.cat_1_task_1.category.workspace.created_by,
                          "pk": self.cat_1_task_1.pk,
                      })
        response = self.client.delete(url)
        task_1_query = self.get_task_query(
            pk_seq=[self.cat_1_task_1.pk])
        assert response.status_code == status.HTTP_204_NO_CONTENT
        self.assertFalse(task_1_query.exists())


class TaskApiConstraintTests(TaskApiFullSetupTestClass):
    """
    Test model constraints.
    """


class TaskApiCleanSaveDeleteTests(TaskApiFullSetupTestClass):
    """
    Test model's `clean`, `save`, `delete` methods
        - validation
        - functionality
    """


class TaskApiTreeTests(TaskApiFullSetupTestClass):
    """
    Test model's tree related
        - validation
        - functionality
    """

    @classmethod
    def db_create_tasks_nested(cls, user, category):
        setattr(cls,
                f'cat_{category.pk}_nested_task_1',
                core_models.Task.objects.create(
                    title="Nested task 1",
                    workspace=category.workspace,
                    category=category,
                ))
        setattr(cls,
                f'cat_{category.pk}_nested_task_1_1',
                core_models.Task.objects.create(
                    title="Nested task 1_1",
                    workspace=category.workspace,
                    category=category,
                    parent=cls.cat_1_nested_task_1,
                ))
        setattr(cls,
                f'cat_{category.pk}_nested_task_1_1_1',
                core_models.Task.objects.create(
                    title="Nested task 1_1_1",
                    workspace=category.workspace,
                    category=category,
                    parent=cls.cat_1_nested_task_1_1,
                ))
        setattr(cls,
                f'cat_{category.pk}_nested_task_1_1_2',
                core_models.Task.objects.create(
                    title="Nested task 1_1_2",
                    workspace=category.workspace,
                    category=category,
                    parent=cls.cat_1_nested_task_1_1,
                ))

    @classmethod
    def setUpTestData(cls):
        """
        Create some nested categories in db.
        """
        super().setUpTestData()
        cls.db_create_tasks_nested(cls.user, cls.ws_1_cat_1)
        cls.db_create_tasks_nested(cls.user, cls.ws_1_cat_2)

    def test_create_post(self):
        data = {
            "title": "task tmp",
            "workspace": self.ws_1_cat_1.workspace.pk,
            "description": "",
            "category": self.ws_1_cat_1.pk,
            "parent": self.cat_1_nested_task_1_1.pk,
            "is_visible": self.cat_1_nested_task_1_1.is_visible,
        }
        url = reverse(self.view_name_list,
                      kwargs={
                          "user_id": self.cat_1_nested_task_1_1.category.workspace.created_by,
                      })
        response = self.client.post(url, data)
        retrieved_data = core_models.Task.objects.filter(
            title="task tmp", parent=self.cat_1_nested_task_1_1)
        assert response.status_code == status.HTTP_201_CREATED
        assert retrieved_data.exists()

    def test_error_parent_same_on_update_patch(self):
        """
        Test task parent is not same on update using patch.
        """
        data = {
            "parent": self.cat_1_nested_task_1_1.pk,
        }
        url = reverse(self.view_name_detail,
                      kwargs={
                          "user_id": self.cat_1_nested_task_1_1.category.workspace.created_by,
                          "pk": self.cat_1_nested_task_1_1.pk,
                      })
        response = self.client.patch(url, data)
        self.cat_1_nested_task_1_1.refresh_from_db()
        task_1_serializer = self.get_task_serializers(
            pk_seq=[self.cat_1_nested_task_1_1.pk])
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Parent cannot be object itself." in response.data[0]

    def test_error_parent_same_on_update_put(self):
        """
        Test task parent is not same on update using put.
        """
        data = {
            "title": "task tmp",
            "workspace": self.ws_1_cat_1.workspace.pk,
            "description": "",
            "category": self.cat_1_nested_task_1_1.category.pk,
            "parent": self.cat_1_nested_task_1_1.pk,
            "is_visible": self.cat_1_nested_task_1_1.is_visible,
        }
        url = reverse(self.view_name_detail,
                      kwargs={
                          "user_id": self.cat_1_nested_task_1_1.category.workspace.created_by,
                          "pk": self.cat_1_nested_task_1_1.pk,
                      })
        response = self.client.put(url, data)
        self.cat_1_nested_task_1_1.refresh_from_db()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Parent cannot be object itself." in response.data[0]

    def test_error_parent_workspace_same_on_create_post(self):
        """
        Test task parent's workspace is same when creating using post.
        Since api does not allow access to different workspace while
        updating a task "invalid pk" error is raised.
        """
        data = {
            "title": "task tmp",
            "workspace": self.ws_1_cat_1.workspace.pk,
            "description": "",
            "category": self.cat_1_nested_task_1_1.category.pk,
            "parent": self.cat_2_nested_task_1.pk,
            "is_visible": self.cat_1_nested_task_1_1.is_visible,
        }
        url = reverse(self.view_name_list,
                      kwargs={
                          "user_id": self.cat_1_nested_task_1_1.category.workspace.created_by,
                      })
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_error_parent_workspace_same_on_update_put(self):
        """
        Test task parent's workspace is same when updating using put.
        Since api does not allow access to different workspace while
        updating a task "invalid pk" error is raised.
        """
        data = {
            "title": "task tmp",
            "workspace": self.ws_1_cat_1.workspace.pk,
            "description": "",
            "category": self.cat_1_nested_task_1_1.category.pk,
            "parent": self.cat_2_nested_task_1.pk,
        }
        url = reverse(self.view_name_detail,
                      kwargs={
                          "user_id": self.cat_1_nested_task_1_1.category.workspace.created_by,
                          "pk": self.cat_1_nested_task_1_1.pk,
                      })
        response = self.client.put(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_visibility_same_as_parent_on_create_post(self):
        data = {
            "title": "task tmp",
            "workspace": self.ws_1_cat_1.workspace.pk,
            "description": "",
            "category": self.ws_1_cat_1.pk,
            "parent": self.cat_1_nested_task_1_1.pk,
            "is_visible": not self.cat_1_nested_task_1_1.is_visible,
        }
        url = reverse(self.view_name_list,
                      kwargs={
                          "user_id": self.cat_1_nested_task_1_1.category.workspace.created_by,
                      })
        response = self.client.post(url, data)
        retrieved_data = core_models.Task.objects.filter(
            title="task tmp", parent=self.cat_1_nested_task_1_1)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Visibility should be same as of parent's." in response.data[0]

    def test_visibility_same_as_parent_on_update_put(self):
        """
        Test task parent's visibility is same when updating using put.
        """
        data = {
            "title": "task tmp",
            "workspace": self.ws_1_cat_1.workspace.pk,
            "description": "",
            "category": self.cat_1_nested_task_1_1.category.pk,
            "parent": self.cat_2_nested_task_1.pk,
            "is_visible": not self.cat_2_nested_task_1.is_visible,
        }
        url = reverse(self.view_name_detail,
                      kwargs={
                          "user_id": self.cat_1_nested_task_1_1.category.workspace.created_by,
                          "pk": self.cat_1_nested_task_1_1.pk,
                      })
        response = self.client.put(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
