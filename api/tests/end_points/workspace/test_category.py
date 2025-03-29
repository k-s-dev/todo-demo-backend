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


class CategoryApiMinimalSetupClass(CustomTestCaseSetup):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = cls.create_user()
        cls.view_name_list = "api:user-category-list"
        cls.view_name_detail = "api:user-category-detail"

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
    def get_category_serializers(cls, pk_seq=None, user_id_seq=None):
        category_query = cls.get_category_query(
            pk_seq=pk_seq, user_id_seq=user_id_seq).order_by("id")
        return api_serializers.CategorySerializer(
            category_query, many=True, context={"request": cls.request_tmp},
        )


class CategoryApiFullSetupTestClass(CategoryApiMinimalSetupClass):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.db_create_workspaces(cls.user)
        for workspace in cls.get_workspace_query():
            cls.db_create_categories(cls.user, workspace)

    def setUp(self):
        super().setUp()


class CategoryApiAuthAndCrudTests(CategoryApiFullSetupTestClass):
    """Test basic auth and CRUD operations on category view api."""

    def test_auth_required(self):
        self.client.force_authenticate(None)
        response = self.client.get(
            reverse(self.view_name_list,
                    kwargs={"user_id": self.ws_1_category_1.workspace.created_by}))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_category_get(self):
        """Test category get."""
        response = self.client.get(reverse(self.view_name_list,
                                           kwargs={"user_id": self.ws_1_category_1.workspace.created_by}))
        response_1 = self.client.get(reverse(self.view_name_detail, kwargs={
            "user_id": self.ws_1_category_1.workspace.created_by,
            "pk": self.ws_1_category_1.pk,
        }))
        category_1_serializer = self.get_category_serializers(
            pk_seq=[self.ws_1_category_1.pk])
        ws_1_serializers = self.get_category_serializers(
            user_id_seq=[self.ws_1_category_1.workspace.created_by])

        assert response.status_code == status.HTTP_200_OK
        assert response.data == ws_1_serializers.data
        assert response_1.data == category_1_serializer.data[0]

    def test_category_create_post(self):
        """
        Test category create post.
        """

        data = {
            "name": "category tmp",
            "description": "",
            "workspace": self.workspace_1.pk,
            "parent": "",
        }
        url = reverse(self.view_name_list, kwargs={
                      "user_id": self.ws_1_category_1.workspace.created_by})
        response = self.client.post(url, data)
        retrieved_data = core_models.Category.objects.filter(
            name="category tmp")
        assert response.status_code == status.HTTP_201_CREATED
        assert retrieved_data.exists()

    def test_category_update_patch(self):
        """Test category update using patch."""
        data = {
            "name": "edit 1",
        }
        url = reverse(self.view_name_detail,
                      kwargs={
                          "user_id": self.ws_1_category_1.workspace.created_by,
                          "pk": self.ws_1_category_1.pk,
                      })
        response = self.client.patch(url, data)
        self.ws_1_category_1.refresh_from_db()
        category_1_serializer = self.get_category_serializers(
            pk_seq=[self.ws_1_category_1.pk])
        assert response.status_code == status.HTTP_200_OK
        assert response.data == category_1_serializer.data[0]

    def test_category_update_put(self):
        """Test category update using put."""
        data = {
            "name": "category tmp",
            "description": "",
            "workspace": self.workspace_1.pk,
            "parent": "",
        }
        url = reverse(self.view_name_detail,
                      kwargs={
                          "user_id": self.ws_1_category_1.workspace.created_by,
                          "pk": self.ws_1_category_1.pk,
                      })
        response = self.client.put(url, data)
        self.ws_1_category_1.refresh_from_db()
        category_1_serializer = self.get_category_serializers(
            pk_seq=[self.ws_1_category_1.pk])
        assert response.status_code == status.HTTP_200_OK
        assert response.data == category_1_serializer.data[0]

    def test_category_delete(self):
        """Test category delete."""
        url = reverse(self.view_name_detail,
                      kwargs={
                          "user_id": self.ws_1_category_1.workspace.created_by,
                          "pk": self.ws_1_category_1.pk,
                      })
        response = self.client.delete(url)
        category_1_query = self.get_category_query(
            pk_seq=[self.ws_1_category_1.pk])
        assert response.status_code == status.HTTP_204_NO_CONTENT
        self.assertFalse(category_1_query.exists())


class CategoryApiConstraintTests(CategoryApiFullSetupTestClass):
    """
    Test model constraints.
    """

    def test_unique_lower_name_workspace_fail_on_duplicate_during_create(self):
        """
        Test that category name is unique for a workspace at time of creation.
        Check that "unique_lower_category_owner_name" error is raised on duplicate.
        """

        url = reverse(self.view_name_list, kwargs={
                      "user_id": self.ws_1_category_1.workspace.created_by})
        data = {
            "name": "category 1",
            "workspace": self.workspace_1.pk,
            "parent": "",
        }
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "unique_lower_category_name_workspace" in response.data[0]

    def test_unique_lower_name_workspace_fail_on_duplicate_during_update_put(self):
        """
        Test that category name is unique for a workspace at time of update using put.
        Check that "unique_lower_category_owner_name" error is raised on duplicate.
        """

        url = reverse(self.view_name_detail,
                      kwargs={
                          "user_id": self.ws_1_category_1.workspace.created_by,
                          "pk": self.ws_1_category_1.pk,
                      })
        data = {
            "name": "category 2",
            "workspace": self.workspace_1.pk,
            "parent": "",
        }
        response = self.client.put(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "unique_lower_category_name_workspace" in response.data[0]

    def test_unique_lower_name_workspace_fail_on_duplicate_during_update_patch(self):
        """
        Test that category name is unique for a workspace at time of update using patch.
        Check that "unique_lower_category_owner_name" error is raised on duplicate.
        """

        url = reverse(self.view_name_detail,
                      kwargs={
                          "user_id": self.ws_1_category_1.workspace.created_by,
                          "pk": self.ws_1_category_1.pk,
                      })
        data = {
            "name": "category 2",
        }
        response = self.client.patch(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "unique_lower_category_name_workspace" in response.data[0]

    def test_unique_lower_name_workspace_allow_duplicate_for_different_workspace(self):
        """
        Check that duplicate name for different workspaces is allowed.
        """

        duplicate_name = "duplicate category across workspace"
        url_1 = reverse(self.view_name_list,
                        kwargs={"user_id": self.ws_1_category_1.workspace.created_by, })
        data_1 = {
            "name": duplicate_name,
            "workspace": self.workspace_1.pk,
            "parent": "",
        }
        url_2 = reverse(self.view_name_list,
                        kwargs={"user_id": self.workspace_2.pk, })
        data_2 = {
            "name": duplicate_name,
            "workspace": self.workspace_2.pk,
            "parent": "",
        }
        response_1 = self.client.post(url_1, data_1)
        response_2 = self.client.post(url_2, data_2)
        assert response_2.status_code == status.HTTP_201_CREATED
        assert "unique_lower_category_name_workspace" not in response_2.data
        assert self.get_category_query().filter(name=duplicate_name).count() == 2


class CategoryApiCleanSaveDeleteTests(CategoryApiFullSetupTestClass):
    """
    Test model's `clean`, `save`, `delete` methods
        - validation
        - functionality
    """


class CategoryApiTreeTests(CategoryApiFullSetupTestClass):
    """
    Test model's tree related
        - validation
        - functionality
    """

    @classmethod
    def db_create_categories_nested(cls, user, workspace):
        setattr(cls,
                f'ws_{workspace.pk}_nested_cat_1',
                core_models.Category.objects.create(
                    name="Nested category 1",
                    workspace=workspace,
                ))
        setattr(cls,
                f'ws_{workspace.pk}_nested_cat_1_1',
                core_models.Category.objects.create(
                    name="Nested category 1_1",
                    workspace=workspace,
                    parent=cls.ws_1_nested_cat_1,
                ))
        setattr(cls,
                f'ws_{workspace.pk}_nested_cat_1_1_1',
                core_models.Category.objects.create(
                    name="Nested category 1_1_1",
                    workspace=workspace,
                    parent=cls.ws_1_nested_cat_1_1,
                ))
        setattr(cls,
                f'ws_{workspace.pk}_nested_cat_1_1_2',
                core_models.Category.objects.create(
                    name="Nested category 1_1_2",
                    workspace=workspace,
                    parent=cls.ws_1_nested_cat_1_1,
                ))

    @classmethod
    def setUpTestData(cls):
        """
        Create some nested categories in db.
        """
        super().setUpTestData()
        cls.db_create_categories_nested(cls.user, cls.workspace_1)
        cls.db_create_categories_nested(cls.user, cls.workspace_2)

    def test_simple_create(self):
        data = {
            "name": "category tmp",
            "description": "",
            "workspace": self.workspace_1.pk,
            "parent": self.ws_1_nested_cat_1_1.pk,
        }
        url = reverse(self.view_name_list, kwargs={
                      "user_id": self.ws_1_nested_cat_1_1.workspace.created_by})
        response = self.client.post(url, data)
        retrieved_data = core_models.Category.objects.filter(
            name="category tmp", parent=self.ws_1_nested_cat_1_1)
        assert response.status_code == status.HTTP_201_CREATED
        assert retrieved_data.exists()

    def test_error_parent_same_on_update_patch(self):
        """
        Test category parent is not same on update using patch.
        """
        data = {
            "parent": self.ws_1_nested_cat_1_1.pk,
        }
        url = reverse(self.view_name_detail,
                      kwargs={
                          "user_id": self.ws_1_category_1.workspace.created_by,
                          "pk": self.ws_1_nested_cat_1_1.pk,
                      })
        response = self.client.patch(url, data)
        self.ws_1_nested_cat_1_1.refresh_from_db()
        category_1_serializer = self.get_category_serializers(
            pk_seq=[self.ws_1_nested_cat_1_1.pk])
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Parent cannot be object itself." in response.data[0]

    def test_error_parent_same_on_update_put(self):
        """
        Test category parent is not same on update using put.
        """
        data = {
            "name": "category tmp",
            "description": "",
            "workspace": self.ws_1_nested_cat_1_1.workspace.pk,
            "parent": self.ws_1_nested_cat_1_1.pk,
        }
        url = reverse(self.view_name_detail,
                      kwargs={
                          "user_id": self.ws_1_category_1.workspace.created_by,
                          "pk": self.ws_1_nested_cat_1_1.pk,
                      })
        response = self.client.put(url, data)
        self.ws_1_nested_cat_1_1.refresh_from_db()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Parent cannot be object itself." in response.data[0]

    def test_error_parent_workspace_same_on_create_post(self):
        """
        Test category parent's workspace is same when creating using post.
        Since api does not allow access to different workspace while
        updating a category "invalid pk" error is raised.
        """
        data = {
            "name": "category tmp",
            "description": "",
            "workspace": self.ws_1_nested_cat_1_1.workspace.created_by,
            "parent": self.ws_2_nested_cat_1.pk,
        }
        url = reverse(self.view_name_list,
                      kwargs={
                          "user_id": self.ws_1_nested_cat_1_1.workspace.created_by,
                      })
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_error_parent_workspace_same_on_update_put(self):
        """
        Test category parent's workspace is same when updating using put.
        Since api does not allow access to different workspace while
        updating a category "invalid pk" error is raised.
        """
        data = {
            "name": "category tmp",
            "description": "",
            "workspace": self.ws_1_nested_cat_1_1.workspace.pk,
            "parent": self.ws_2_nested_cat_1.pk,
        }
        url = reverse(self.view_name_detail,
                      kwargs={
                          "pk": self.ws_1_nested_cat_1_1.pk,
                          "user_id": self.ws_1_nested_cat_1_1.workspace.created_by,
                      })
        response = self.client.put(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
