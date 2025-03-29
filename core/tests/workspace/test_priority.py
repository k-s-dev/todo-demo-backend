from django.core.exceptions import ValidationError
from django.db import IntegrityError
from core import models as core_models
from ..generic_classes import CustomTestCaseSetup


class PriorityModelMinimalSetupClass(CustomTestCaseSetup):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def setUp(self):
        super().setUp()


class PriorityModelFullSetupTestClass(PriorityModelMinimalSetupClass):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.db_create_workspaces(cls.user)
        for workspace in cls.get_workspace_query():
            cls.db_create_priorities(cls.user, workspace)

    def setUp(self):
        super().setUp()


class PriorityModelAuthAndCrudTests(PriorityModelFullSetupTestClass):
    """Test basic auth and CRUD operations on priority view."""

    def test_priority_create(self):
        """
        Test priority create.
        """

        priority = core_models.Priority.objects.create(
            name="Priority tmp",
            workspace=self.workspace_1,
        )
        assert core_models.Priority.objects.filter(name="Priority tmp").exists()

    def test_priority_read(self):
        """Test priority read."""

        assert core_models.Priority.objects.filter(name=self.ws_1_priority_1.name).exists()

    def test_priority_update(self):
        """Test priority update."""

        self.ws_1_priority_1.name = "random"
        self.ws_1_priority_1.save(force_update=True)
        self.ws_1_priority_1.refresh_from_db()
        assert self.ws_1_priority_1.name == "random"

    def test_priority_delete(self):
        """Test priority delete."""

        self.ws_1_priority_1.delete()
        priority_1_query = self.get_priority_query(pk_seq=[self.ws_1_priority_1.pk])
        self.assertFalse(priority_1_query.exists())


class PriorityModelConstraintTests(PriorityModelFullSetupTestClass):
    """
    Test model constraints.
    """

    def test_unique_lower_name_workspace_fail_on_duplicate_during_create(self):
        """
        Test that priority name is unique for a workspace at time of creation.
        Check that "unique_lower_priority_owner_name" error is raised on duplicate.
        """

        msg = "unique_lower_priority_name_workspace"
        try:
            priority = core_models.Priority.objects.create(
                name="Priority 1",
                workspace=self.workspace_1,
            )
        except IntegrityError as e:
            self.assertRaises(IntegrityError)
            assert msg in str(e)

    def test_lower_name_workspace_fail_on_duplicate_during_update(self):
        """
        Test that priority name is unique for a workspace at time of update.
        Check that "unique_lower_priority_name_workspace" error is raised on duplicate.
        """

        msg = "unique_lower_priority_name_workspace"
        self.ws_1_priority_1.name = self.ws_1_priority_2.name
        try:
            self.ws_1_priority_1.full_clean()
        except ValidationError as e:
            self.assertRaises(ValidationError)
            assert msg in str(e)

    def test_unique_lower_name_workspace_allow_duplicate_for_different_workspace(self):
        """
        Check that duplicate name for different workspaces is allowed.
        """

        self.ws_1_priority_1.name = "Unique"
        self.ws_1_priority_1.save()
        self.ws_2_priority_1.name = "Unique"
        self.ws_2_priority_1.full_clean()
        self.ws_2_priority_1.save()
        assert self.ws_2_priority_1.name == "Unique"


class PriorityModelCleanSaveDeleteTests(PriorityModelFullSetupTestClass):
    """
    Test model's `clean`, `save`, `delete` methods
        - validation
        - functionality
    """
