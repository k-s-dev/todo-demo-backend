from django.core.exceptions import ValidationError
from django.db import IntegrityError
from core import models as core_models
from ..generic_classes import CustomTestCaseSetup


class TagModelMinimalSetupClass(CustomTestCaseSetup):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def setUp(self):
        super().setUp()


class TagModelFullSetupTestClass(TagModelMinimalSetupClass):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.db_create_workspaces(cls.user)
        for workspace in cls.get_workspace_query():
            cls.db_create_tags(cls.user, workspace)

    def setUp(self):
        super().setUp()


class TagModelAuthAndCrudTests(TagModelFullSetupTestClass):
    """Test basic auth and CRUD operations on tag view."""

    def test_tag_create(self):
        """
        Test tag create.
        """

        tag = core_models.Tag.objects.create(
            name="Tag tmp",
            workspace=self.workspace_1,
        )
        assert core_models.Tag.objects.filter(name="Tag tmp").exists()

    def test_tag_read(self):
        """Test tag read."""

        assert core_models.Tag.objects.filter(
            name=self.ws_1_tag_1.name).exists()

    def test_tag_update(self):
        """Test tag update."""

        self.ws_1_tag_1.name = "random"
        self.ws_1_tag_1.save(force_update=True)
        self.ws_1_tag_1.refresh_from_db()
        assert self.ws_1_tag_1.name == "random"

    def test_tag_delete(self):
        """Test tag delete."""

        self.ws_1_tag_1.delete()
        tag_1_query = self.get_tag_query(pk_seq=[self.ws_1_tag_1.pk])
        self.assertFalse(tag_1_query.exists())


class TagModelConstraintTests(TagModelFullSetupTestClass):
    """
    Test model constraints.
    """

    def test_unique_lower_name_workspace_fail_on_duplicate_during_create(self):
        """
        Test that tag name is unique for a workspace at time of creation.
        Check that "unique_lower_tag_owner_name" error is raised on duplicate.
        """

        msg = "unique_lower_tag_name_workspace"
        try:
            tag = core_models.Tag.objects.create(
                name="Tag 1",
                workspace=self.workspace_1,
            )
        except IntegrityError as e:
            self.assertRaises(IntegrityError)
            assert msg in str(e)

    def test_lower_name_workspace_fail_on_duplicate_during_update(self):
        """
        Test that tag name is unique for a workspace at time of update.
        Check that "unique_lower_tag_name_workspace" error is raised on duplicate.
        """

        msg = "unique_lower_tag_name_workspace"
        self.ws_1_tag_1.name = self.ws_1_tag_2.name
        try:
            self.ws_1_tag_1.full_clean()
        except ValidationError as e:
            self.assertRaises(ValidationError)
            assert msg in str(e)

    def test_unique_lower_name_workspace_allow_duplicate_for_different_workspace(self):
        """
        Check that duplicate name for different workspaces is allowed.
        """

        self.ws_1_tag_1.name = "Unique"
        self.ws_1_tag_1.save()
        self.ws_2_tag_1.name = "Unique"
        self.ws_2_tag_1.full_clean()
        self.ws_2_tag_1.save()
        assert self.ws_2_tag_1.name == "Unique"


class TagModelCleanSaveDeleteTests(TagModelFullSetupTestClass):
    """
    Test model's `clean`, `save`, `delete` methods
        - validation
        - functionality
    """
