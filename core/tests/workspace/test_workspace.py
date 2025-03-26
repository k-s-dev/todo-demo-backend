from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from core import models as core_models
from ..generic_classes import CustomTestCaseSetup


class WorkspaceModelMinimalSetupClass(CustomTestCaseSetup):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def setUp(self):
        super().setUp()


class WorkspaceModelFullSetupTestClass(WorkspaceModelMinimalSetupClass):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.db_create_workspaces(cls.user)

    def setUp(self):
        super().setUp()


class WorkspaceModelCrudTests(WorkspaceModelFullSetupTestClass):
    """Test CRUD operations on workspace model through orm."""

    def test_workspace_create(self):
        """
        Test workspace create.
        """

        workspace = core_models.Workspace.objects.create(
            name="Workspace tmp",
            created_by=self.user.id,
        )
        assert workspace.name == "Workspace tmp"
        assert not workspace.is_default

    def test_workspace_read(self):
        """Test workspace read."""

        assert self.workspace_1.name == "workspace 1"
        assert self.workspace_1.is_default

    def test_workspace_update(self):
        """Test workspace update."""

        self.workspace_1.name = "default"
        self.workspace_1.save(force_update=True)
        self.workspace_1.refresh_from_db()
        assert self.workspace_1.name == "default"

    def test_workspace_delete(self):
        """Test workspace delete."""
        self.workspace_1.delete()
        workspace_1_query = self.get_workspace_query(
            pk_seq=[self.workspace_1.pk])
        self.assertFalse(workspace_1_query.exists())


class WorkspaceModelConstraintTests(WorkspaceModelFullSetupTestClass):
    """
    Test model constraints.
    """

    def test_unique_lower_name_created_by_fail_on_duplicate(self):
        """
        Test that workspace name is unique for a user at time of creation.
        Check that "unique_lower_workspace_owner_name" error is raised on duplicate.
        """

        msg = "unique_lower_workspace_owner_name"
        try:
            workspace = core_models.Workspace.objects.create(
                name="Workspace 1",
                created_by=self.user.id,
            )
        except IntegrityError as e:
            self.assertRaises(IntegrityError)
            assert msg in str(e)

    def test_unique_lower_name_created_by_allow_duplicate_for_different_user(self):
        """
        Test that workspace name is unique for a user at time of creation.
        Check that duplicate name for different users is allowed.
        """

        user_2 = self.create_user("user-2", "testpassword234")
        workspace = core_models.Workspace.objects.create(
            name="Workspace 1",
            created_by=user_2.id,
        )
        assert workspace.name == "Workspace 1"
        assert workspace.created_by == user_2.id


class WorkspaceModelCleanSaveDeleteTests(WorkspaceModelFullSetupTestClass):
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

        self.workspace_2.delete()
        self.workspace_1.is_default = False
        try:
            self.workspace_1.full_clean()
        except ValidationError as e:
            assert "There has to be at-least one default workspace." in str(e)

    def test_error_ensure_atleast_one_default_on_updates_with_multiple_workspaces(self):
        """
        Test that if
            - there are multiple workspaces
            - default workspace is updated to be non-default
            - error is raised with message
        """

        self.workspace_1.is_default = False
        try:
            self.workspace_1.full_clean()
        except ValidationError as e:
            assert "There has to be at-least one default workspace." in str(e)

    def test_swap_ensure_only_one_default_on_updates_with_multiple_workspaces(self):
        """
        Test that if
            - there are multiple workspaces
            - non-default workspace is updated to be default
            - original default is made non-default
        """

        self.workspace_2.is_default = True
        self.workspace_2.save()
        self.workspace_1.refresh_from_db()
        self.assertFalse(self.workspace_1.is_default)


class WorkspaceModelCleanSaveDeleteIsolatedTests(WorkspaceModelMinimalSetupClass):
    """
    Test model's `clean`, `save`, `delete` method functionality.
    """

    def test_first_workspace_without_default_made_default(self):
        """
        Test that first workspace created for a user is made default
        even if set as non-default.
        """

        workspace = core_models.Workspace.objects.create(
            name="Workspace 1",
            created_by=self.user.id,
        )
        assert workspace.is_default
