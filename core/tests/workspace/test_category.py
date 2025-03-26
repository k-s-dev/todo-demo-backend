from django.core.exceptions import ValidationError
from django.db import IntegrityError
from core import models as core_models
from ..generic_classes import CustomTestCaseSetup


class CategoryModelMinimalSetupClass(CustomTestCaseSetup):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def setUp(self):
        super().setUp()


class CategoryModelFullSetupTestClass(CategoryModelMinimalSetupClass):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.db_create_workspaces(cls.user)
        for workspace in cls.get_workspace_query():
            cls.db_create_categories(cls.user, workspace)

    def setUp(self):
        super().setUp()


class CategoryModelAuthAndCrudTests(CategoryModelFullSetupTestClass):
    """Test basic auth and CRUD operations on category view."""

    def test_category_create(self):
        """
        Test category create.
        """

        category = core_models.Category.objects.create(
            name="Category tmp",
            workspace=self.workspace_1,
        )
        assert core_models.Category.objects.filter(name="Category tmp").exists()

    def test_category_read(self):
        """Test category read."""

        assert core_models.Category.objects.filter(
            name=self.ws_1_category_1.name).exists()

    def test_category_update(self):
        """Test category update."""

        self.ws_1_category_1.name = "random"
        self.ws_1_category_1.save(force_update=True)
        self.ws_1_category_1.refresh_from_db()
        assert self.ws_1_category_1.name == "random"

    def test_category_delete(self):
        """Test category delete."""

        self.ws_1_category_1.delete()
        category_1_query = self.get_category_query(pk_seq=[self.ws_1_category_1.pk])
        self.assertFalse(category_1_query.exists())


class CategoryModelConstraintTests(CategoryModelFullSetupTestClass):
    """
    Test model constraints.
    """

    def test_unique_lower_name_workspace_fail_on_duplicate_during_create(self):
        """
        Test that category name is unique for a workspace at time of creation.
        Check that "unique_lower_category_owner_name" error is raised on duplicate.
        """

        msg = "unique_lower_category_name_workspace"
        try:
            category = core_models.Category.objects.create(
                name="Category 1",
                workspace=self.workspace_1,
            )
        except IntegrityError as e:
            self.assertRaises(IntegrityError)
            assert msg in str(e)

    def test_lower_name_workspace_fail_on_duplicate_during_update(self):
        """
        Test that category name is unique for a workspace at time of update.
        Check that "unique_lower_category_name_workspace" error is raised on duplicate.
        """

        msg = "unique_lower_category_name_workspace"
        self.ws_1_category_1.name = self.ws_1_category_2.name
        try:
            self.ws_1_category_1.full_clean()
        except ValidationError as e:
            self.assertRaises(ValidationError)
            assert msg in str(e)

    def test_unique_lower_name_workspace_allow_duplicate_for_different_workspace(self):
        """
        Check that duplicate name for different workspaces is allowed.
        """

        self.ws_1_category_1.name = "Unique"
        self.ws_1_category_1.save()
        self.ws_2_category_1.name = "Unique"
        self.ws_2_category_1.full_clean()
        self.ws_2_category_1.save()
        assert self.ws_2_category_1.name == "Unique"


class CategoryModelCleanSaveDeleteTests(CategoryModelFullSetupTestClass):
    """
    Test model's `clean`, `save`, `delete` methods
        - validation
        - functionality
    """


class CategoryModelTreeTests(CategoryModelFullSetupTestClass):
    """
    Test model's tree related
        - validation
        - functionality
    """

    @classmethod
    def db_create_categories_nested(cls, user, workspace):
        prefix = f'ws_{workspace.pk}_nested_category'
        setattr(cls,
                f'{prefix}_1',
                core_models.Category.objects.create(
                    name="Nested category 1",
                    workspace=workspace,
                ))
        setattr(cls,
                f'{prefix}_1_1',
                core_models.Category.objects.create(
                    name="Nested category 1_1",
                    workspace=workspace,
                    parent=cls.ws_1_nested_category_1,
                ))
        setattr(cls,
                f'{prefix}_1_1_1',
                core_models.Category.objects.create(
                    name="Nested category 1_1_1",
                    workspace=workspace,
                    parent=cls.ws_1_nested_category_1_1,
                ))
        setattr(cls,
                f'{prefix}_1_1_2',
                core_models.Category.objects.create(
                    name="Nested category 1_1_2",
                    workspace=workspace,
                    parent=cls.ws_1_nested_category_1_1,
                ))

    @classmethod
    def setUpTestData(cls):
        """
        Create some nested categories in db.
        """
        super().setUpTestData()
        cls.db_create_categories_nested(cls.user, cls.workspace_1)
        cls.db_create_categories_nested(cls.user, cls.workspace_2)

    msg_parent = "Parent cannot be object itself."
    msg_parent_attribute = "Workspace should be same as parent's."

    def test_create(self):
        assert self.ws_1_nested_category_1.name == "Nested category 1"

    def test_error_parent_same_on_update(self):
        """
        Test category parent is not same on update using patch.
        """

        self.ws_1_nested_category_1_1.parent = self.ws_1_nested_category_1_1
        try:
            self.ws_1_nested_category_1_1.full_clean()
        except ValidationError as e:
            assert self.msg_parent in str(e)

    def test_error_parent_workspace_same_on_create(self):
        """
        Test category parent's workspace is same when creating.
        """

        try:
            core_models.Category.objects.create(
                name="category tmp",
                workspace=self.workspace_1,
                parent=self.ws_2_nested_category_1,
            )
        except ValidationError as e:
            assert self.msg_parent_attribute in str(e)

    def test_error_parent_workspace_same_on_update(self):
        """
        Test category parent's workspace is same when updating using put.
        """

        self.ws_1_nested_category_1_1.parent = self.ws_2_nested_category_1
        try:
            self.ws_1_nested_category_1_1.full_clean()
        except ValidationError as e:
            assert self.msg_parent_attribute in str(e)
