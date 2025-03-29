from django.core.exceptions import ValidationError
from django.db import IntegrityError
from core import models as core_models
from ..generic_classes import CustomTestCaseSetup


class StatusModelMinimalSetupClass(CustomTestCaseSetup):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def setUp(self):
        super().setUp()


class StatusModelFullSetupTestClass(StatusModelMinimalSetupClass):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.db_create_workspaces(cls.user)
        for workspace in cls.get_workspace_query():
            cls.db_create_statuses(cls.user, workspace)

    def setUp(self):
        super().setUp()


class StatusModelAuthAndCrudTests(StatusModelFullSetupTestClass):
    """Test basic auth and CRUD operations on status view."""

    def test_status_create(self):
        """
        Test status create.
        """

        status = core_models.Status.objects.create(
            name="Status tmp",
            workspace=self.workspace_1,
        )
        assert core_models.Status.objects.filter(name="Status tmp").exists()

    def test_status_read(self):
        """Test status read."""

        assert core_models.Status.objects.filter(
            name=self.ws_1_status_1.name).exists()

    def test_status_update(self):
        """Test status update."""

        self.ws_1_status_1.name = "random"
        self.ws_1_status_1.save(force_update=True)
        self.ws_1_status_1.refresh_from_db()
        assert self.ws_1_status_1.name == "random"

    def test_status_delete(self):
        """Test status delete."""

        self.ws_1_status_1.delete()
        status_1_query = self.get_status_query(pk_seq=[self.ws_1_status_1.pk])
        self.assertFalse(status_1_query.exists())


class StatusModelConstraintTests(StatusModelFullSetupTestClass):
    """
    Test model constraints.
    """

    def test_unique_lower_name_workspace_fail_on_duplicate_during_create(self):
        """
        Test that status name is unique for a workspace at time of creation.
        Check that "unique_lower_status_owner_name" error is raised on duplicate.
        """

        msg = "unique_lower_status_name_workspace"
        try:
            status = core_models.Status.objects.create(
                name="Status 1",
                workspace=self.workspace_1,
            )
        except IntegrityError as e:
            self.assertRaises(IntegrityError)
            assert msg in str(e)

    def test_lower_name_workspace_fail_on_duplicate_during_update(self):
        """
        Test that status name is unique for a workspace at time of update.
        Check that "unique_lower_status_name_workspace" error is raised on duplicate.
        """

        msg = "unique_lower_status_name_workspace"
        self.ws_1_status_1.name = self.ws_1_status_2.name
        try:
            self.ws_1_status_1.full_clean()
        except ValidationError as e:
            self.assertRaises(ValidationError)
            assert msg in str(e)

    def test_unique_lower_name_workspace_allow_duplicate_for_different_workspace(self):
        """
        Check that duplicate name for different workspaces is allowed.
        """

        self.ws_1_status_1.name = "Unique"
        self.ws_1_status_1.save()
        self.ws_2_status_1.name = "Unique"
        self.ws_2_status_1.full_clean()
        self.ws_2_status_1.save()
        assert self.ws_2_status_1.name == "Unique"


class StatusModelCleanSaveDeleteTests(StatusModelFullSetupTestClass):
    """
    Test model's `clean`, `save`, `delete` methods
        - validation
        - functionality
    """
