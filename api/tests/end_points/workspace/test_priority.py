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


class PriorityApiMinimalSetupClass(CustomTestCaseSetup):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = cls.create_user()
        cls.view_name_list = "api:user-priority-list"
        cls.view_name_detail = "api:user-priority-detail"

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
    def get_priority_query(pk_seq=None, user_id_seq=None):
        qry = core_models.Priority.objects.all()
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
    def get_priority_serializers(cls, pk_seq=None, user_id_seq=None):
        priority_query = cls.get_priority_query(
            pk_seq, user_id_seq).order_by("id")
        return api_serializers.PrioritySerializer(
            priority_query, many=True, context={"request": cls.request_tmp},
        )


class PriorityApiFullSetupTestClass(PriorityApiMinimalSetupClass):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.db_create_workspaces(cls.user)
        for workspace in cls.get_workspace_query():
            cls.db_create_priorities(cls.user, workspace)

    def setUp(self):
        super().setUp()


class PriorityApiAuthAndCrudTests(PriorityApiFullSetupTestClass):
    """Test basic auth and CRUD operations on priority view api."""

    def test_auth_required(self):
        self.client.force_authenticate(None)
        response = self.client.get(
            reverse(self.view_name_list,
                    kwargs={"user_id": self.ws_1_priority_1.workspace.created_by})
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_priority_get(self):
        """Test priority get."""
        response = self.client.get(reverse(self.view_name_list,
                                           kwargs={"user_id": self.ws_1_priority_1.workspace.created_by}))
        response_1 = self.client.get(reverse(self.view_name_detail, kwargs={
            "user_id": self.ws_1_priority_1.workspace.created_by,
            "pk": self.ws_1_priority_1.pk,
        }))
        priority_1_serializer = self.get_priority_serializers(
            pk_seq=[self.ws_1_priority_1.pk])
        ws_1_priority_serializers = self.get_priority_serializers(
            user_id_seq=[self.ws_1_priority_1.workspace.created_by])

        assert response.status_code == status.HTTP_200_OK
        assert response.data == ws_1_priority_serializers.data
        assert response_1.data == priority_1_serializer.data[0]

    def test_priority_create_post(self):
        """
        Test priority create post.
        """
        data = {
            "name": "priority tmp",
            "workspace": self.workspace_1.pk,
        }
        url = reverse(self.view_name_list, kwargs={
            "user_id": self.ws_1_priority_1.workspace.created_by})
        response = self.client.post(url, data)
        retrieved_data = core_models.Priority.objects.filter(
            name="priority tmp")
        assert response.status_code == status.HTTP_201_CREATED
        assert retrieved_data.exists()

    def test_priority_update_patch(self):
        """Test priority update using patch."""
        data = {
            "name": "edit 1",
        }
        url = reverse(self.view_name_detail,
                      kwargs={
                          "user_id": self.ws_1_priority_1.workspace.created_by,
                          "pk": self.ws_1_priority_1.pk,
                      })
        response = self.client.patch(url, data)
        self.ws_1_priority_1.refresh_from_db()
        priority_1_serializer = self.get_priority_serializers(
            pk_seq=[self.ws_1_priority_1.pk])
        assert response.status_code == status.HTTP_200_OK
        assert response.data == priority_1_serializer.data[0]

    def test_priority_update_put(self):
        """Test priority update using put."""
        data = {
            "name": "default",
            "workspace": self.workspace_1.pk,
        }
        url = reverse(self.view_name_detail,
                      kwargs={
                          "user_id": self.ws_1_priority_1.workspace.created_by,
                          "pk": self.ws_1_priority_1.pk,
                      })
        response = self.client.put(url, data)
        self.ws_1_priority_1.refresh_from_db()
        priority_1_serializer = self.get_priority_serializers(
            pk_seq=[self.ws_1_priority_1.pk])
        assert response.status_code == status.HTTP_200_OK
        assert response.data == priority_1_serializer.data[0]

    def test_priority_delete(self):
        """Test priority delete."""
        url = reverse(self.view_name_detail,
                      kwargs={
                          "user_id": self.ws_1_priority_1.workspace.created_by,
                          "pk": self.ws_1_priority_1.pk,
                      })
        response = self.client.delete(url)
        priority_1_query = self.get_priority_query(
            pk_seq=[self.ws_1_priority_1.pk])
        assert response.status_code == status.HTTP_204_NO_CONTENT
        self.assertFalse(priority_1_query.exists())


class PriorityApiConstraintTests(PriorityApiFullSetupTestClass):
    """
    Test model constraints.
    """

    def test_unique_lower_name_workspace_fail_on_duplicate_during_create(self):
        """
        Test that priority name is unique for a workspace at time of creation.
        Check that "unique_lower_priority_owner_name" error is raised on duplicate.
        """

        url = reverse(self.view_name_list, kwargs={
            "user_id": self.ws_1_priority_1.workspace.created_by})
        data = {
            "name": "priority 1",
            "workspace": self.workspace_1.pk,
        }
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "unique_lower_priority_name_workspace" in response.data[0]

    def test_unique_lower_name_workspace_fail_on_duplicate_during_update_put(self):
        """
        Test that priority name is unique for a workspace at time of update using put.
        Check that "unique_lower_priority_owner_name" error is raised on duplicate.
        """

        url = reverse(self.view_name_detail,
                      kwargs={
                          "user_id": self.ws_1_priority_1.workspace.created_by,
                          "pk": self.ws_1_priority_1.pk,
                      })
        data = {
            "name": "priority 2",
            "workspace": self.workspace_1.pk,
        }
        response = self.client.put(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "unique_lower_priority_name_workspace" in response.data[0]

    def test_unique_lower_name_workspace_fail_on_duplicate_during_update_patch(self):
        """
        Test that priority name is unique for a workspace at time of update using patch.
        Check that "unique_lower_priority_owner_name" error is raised on duplicate.
        """

        url = reverse(self.view_name_detail,
                      kwargs={
                          "user_id": self.ws_1_priority_1.workspace.created_by,
                          "pk": self.ws_1_priority_1.pk,
                      })
        data = {
            "name": "priority 2",
        }
        response = self.client.patch(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "unique_lower_priority_name_workspace" in response.data[0]

    def test_unique_lower_name_workspace_allow_duplicate_for_different_workspace(self):
        """
        Check that duplicate name for different workspaces is allowed.
        """

        duplicate_name = "duplicate priority across workspace"
        url_1 = reverse(self.view_name_list,
                        kwargs={"user_id": self.ws_1_priority_1.workspace.created_by, })
        data_1 = {
            "name": duplicate_name,
            "workspace": self.workspace_1.pk,
        }
        url_2 = reverse(self.view_name_list,
                        kwargs={"user_id": self.workspace_2.created_by, })
        data_2 = {
            "name": duplicate_name,
            "workspace": self.workspace_2.pk,
        }
        response_1 = self.client.post(url_1, data_1)
        response_2 = self.client.post(url_2, data_2)
        assert response_2.status_code == status.HTTP_201_CREATED
        assert "unique_lower_priority_name_workspace" not in response_2.data
        assert self.get_priority_query().filter(name=duplicate_name).count() == 2


class PriorityApiCleanSaveDeleteTests(PriorityApiFullSetupTestClass):
    """
    Test model's `clean`, `save`, `delete` methods
        - validation
        - functionality
    """
