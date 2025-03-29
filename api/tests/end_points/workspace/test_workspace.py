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
            username=username, password=password, is_superuser=True,
        )


class WorkspaceApiMinimalSetupClass(CustomTestCaseSetup):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = cls.create_user()
        cls.view_name_list = "api:workspace-list"
        cls.view_name_detail = "api:workspace-detail"

    def setUp(self):
        super().setUp()
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_authenticate(self.user)

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

    @staticmethod
    def get_workspace_query(pk_seq=None):
        if pk_seq:
            return core_models.Workspace.objects.filter(pk__in=pk_seq)
        return core_models.Workspace.objects.all()

    @classmethod
    def get_workpace_serializers(cls, pk_seq=None):
        workspace_query = cls.get_workspace_query(pk_seq).order_by("id")
        return api_serializers.WorkspaceSerializer(
            workspace_query, many=True, context={"request": cls.request_tmp})


class WorkspaceApiFullSetupTestClass(WorkspaceApiMinimalSetupClass):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.db_create_workspaces(cls.user)

    def setUp(self):
        super().setUp()


class WorkspaceApiAuthAndCrudTests(WorkspaceApiFullSetupTestClass):
    """Test basic auth and CRUD operations on workspace view api."""

    def test_auth_required(self):
        self.client.force_authenticate(None)
        response = self.client.get(
            reverse(self.view_name_list,
                    kwargs={"user_id": self.user.id})
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_workspace_get(self):
        """Test workspace get."""
        response = self.client.get(
            reverse(self.view_name_list,
                    kwargs={"user_id": self.user.id})
        )
        response_1 = self.client.get(reverse(self.view_name_detail, kwargs={
            "user_id": self.user.id,
            "pk": self.workspace_1.pk,
        }))
        workspace_1_serializer = self.get_workpace_serializers(
            pk_seq=[self.workspace_1.pk])
        assert response.status_code == status.HTTP_200_OK
        assert response.data == self.get_workpace_serializers().data
        assert response_1.data == workspace_1_serializer.data[0]

    def test_workspace_create_post(self):
        """
        Test workspace create post.
        """
        data = {
            "name": "ws tmp",
            "created_by": self.user.id,
        }
        url = reverse(self.view_name_list, kwargs={"user_id": self.user.id, })
        response = self.client.post(url, data)
        retrieved_data = core_models.Workspace.objects.filter(name="ws tmp")
        assert retrieved_data.exists()
        assert response.status_code == status.HTTP_201_CREATED

    def test_workspace_update_patch(self):
        """Test workspace update using patch."""
        data = {
            "description": "edit 1",
        }
        url = reverse(self.view_name_detail,
                      kwargs={
                          "user_id": self.user.id,
                          "pk": self.workspace_1.pk,
                      })
        response = self.client.patch(url, data)
        self.workspace_1.refresh_from_db()
        workspace_1_serializer = self.get_workpace_serializers(
            pk_seq=[self.workspace_1.pk])
        assert response.status_code == status.HTTP_200_OK
        assert response.data == workspace_1_serializer.data[0]

    def test_workspace_update_put(self):
        """Test workspace update using put."""
        data = {
            "name": "default",
            "description": "edit 1",
            "is_default": True,
            "created_by": self.user.id,
        }
        url = reverse(self.view_name_detail,
                      kwargs={
                          "user_id": self.user.id,
                          "pk": self.workspace_1.pk,
                      })
        response = self.client.put(url, data)
        self.workspace_1.refresh_from_db()
        workspace_1_serializer = self.get_workpace_serializers(
            pk_seq=[self.workspace_1.pk])
        assert response.status_code == status.HTTP_200_OK
        assert response.data == workspace_1_serializer.data[0]

    def test_workspace_delete(self):
        """Test workspace delete."""
        url = reverse(self.view_name_detail,
                      kwargs={
                          "user_id": self.user.id,
                          "pk": self.workspace_1.pk,
                      })
        response = self.client.delete(url)
        workspace_1_query = self.get_workspace_query(
            pk_seq=[self.workspace_1.pk])
        assert response.status_code == status.HTTP_204_NO_CONTENT
        self.assertFalse(workspace_1_query.exists())


class WorkspaceApiConstraintTests(WorkspaceApiFullSetupTestClass):
    """
    Test model constraints.
    """

    def test_unique_lower_name_created_by_fail_on_duplicate(self):
        """
        Test that workspace name is unique for a user at time of creation.
        Check that "unique_lower_workspace_owner_name" error is raised on duplicate.
        """

        url = reverse(self.view_name_list, kwargs={"user_id": self.user.id, })
        data = {
            "name": "default",
            "created_by": self.user.id,
        }
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "unique_lower_workspace_owner_name" in response.data[0]

    def test_unique_lower_name_created_by_allow_duplicate_for_different_user(self):
        """
        Test that workspace name is unique for a user at time of creation.
        Check that duplicate name for different users is allowed.
        """

        user_2 = self.create_user("user-2", "testpassword234")
        self.client.force_authenticate(user_2)
        url = reverse(self.view_name_list, kwargs={"user_id": self.user.id, })
        data = {"name": "default", "created_by": user_2.id}
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert core_models.Workspace.objects\
            .filter(name="default", created_by=user_2.id).exists()


class WorkspaceApiCleanSaveDeleteTests(WorkspaceApiFullSetupTestClass):
    """
    Test model's `clean`, `save`, `delete` methods
        - validation
        - functionality
    """

    def test_error_ensure_atleast_one_default_on_updates_with_single_workspace(self):
        """
        Test that if
            - there is single workspace which is default
            - it is updated to be non-default
            - error is raised with message
        """

        workspace_default = self.get_workspace_query().get(is_default=True)
        url = reverse(self.view_name_detail,
                      kwargs={
                          "user_id": workspace_default.created_by,
                          "pk": workspace_default.pk})
        data = {
            "name": "default",
            "description": "",
            "is_default": False,
        }
        response = self.client.patch(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert self.get_workspace_query().get(name="default").is_default
        assert "There has to be at-least one default workspace." in response.data[0]

    def test_error_ensure_atleast_one_default_on_updates_with_multiple_workspaces(self):
        """
        Test that if
            - there are multiple workspaces
            - default workspace is updated to be non-default
            - error is raised with message
        """

        workspace_default = self.get_workspace_query().get(is_default=True)
        url = reverse(self.view_name_detail, kwargs={
            "user_id": self.user.id, "pk": workspace_default.pk})
        data = {
            "name": "default",
            "description": "",
            "is_default": False,
        }
        response = self.client.patch(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert self.get_workspace_query().get(name="default").is_default
        assert "There has to be at-least one default workspace." in response.data[0]

    def test_swap_ensure_only_one_default_on_updates_with_multiple_workspaces(self):
        """
        Test that if
            - there are multiple workspaces
            - non-default workspace is updated to be default
            - original default is made non-default
        """

        default_pk = self.get_workspace_query().get(is_default=True).pk
        non_default_pk = self.get_workspace_query().get(is_default=False).pk
        url = reverse(self.view_name_detail, kwargs={
            "user_id": self.user.id, "pk": non_default_pk})
        data = {
            "is_default": True,
        }
        response = self.client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert self.get_workspace_query().get(pk=non_default_pk).is_default
        self.assertFalse(self.get_workspace_query().get(
            pk=default_pk).is_default)


class WorkspaceApiCleanSaveDeleteIsolatedTests(WorkspaceApiMinimalSetupClass):
    """
    Test model's `clean`, `save`, `delete` method functionality.
    """

    def test_first_workspace_without_default_made_default(self):
        """
        Test that first workspace created for a user is made default
        even if set as non-default.
        """
        url = reverse(self.view_name_list, kwargs={"user_id": self.user.id,})
        data = {
            "name": "default",
            "description": "",
            "is_default": False,
            "created_by": self.user.id,
        }
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert self.get_workspace_query().get(name="default").is_default
