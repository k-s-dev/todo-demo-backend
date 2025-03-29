from django.core.exceptions import ValidationError
from django.db import IntegrityError
from core import models as core_models
from ..generic_classes import CustomTestCaseSetup


class ProjectModelMinimalSetupClass(CustomTestCaseSetup):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def setUp(self):
        super().setUp()


class ProjectModelFullSetupTestClass(ProjectModelMinimalSetupClass):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.db_create_workspaces(cls.user)
        for workspace in cls.get_workspace_query():
            cls.db_create_categories(cls.user, workspace)
        for category in cls.get_category_query():
            cls.db_create_projects(cls.user, category)

    def setUp(self):
        super().setUp()


class ProjectModelAuthAndCrudTests(ProjectModelFullSetupTestClass):
    """Test basic auth and CRUD operations on project view."""

    def test_project_create(self):
        """
        Test project create.
        """

        project = core_models.Project.objects.create(
            title="Project tmp",
            workspace=self.workspace_1,
            category=self.ws_1_category_1,
        )
        assert core_models.Project.objects.filter(title="Project tmp").exists()

    def test_project_read(self):
        """Test project read."""

        assert core_models.Project.objects.filter(
            title=self.cat_1_project_1.title).exists()

    def test_project_update(self):
        """Test project update."""

        self.cat_1_project_1.title = "random"
        self.cat_1_project_1.save(force_update=True)
        self.cat_1_project_1.refresh_from_db()
        assert self.cat_1_project_1.title == "random"

    def test_project_delete(self):
        """Test project delete."""

        self.cat_1_project_1.delete()
        project_1_query = self.get_project_query(
            pk_seq=[self.cat_1_project_1.pk])
        self.assertFalse(project_1_query.exists())


class ProjectModelConstraintTests(ProjectModelFullSetupTestClass):
    """
    Test model constraints.
    """

    msg = "unique_lower_project_title_category_workspace"

    def test_unique_lower_name_workspace_fail_on_duplicate_during_create(self):
        """
        Test that project name is unique for a workspace at time of creation.
        Check that "unique_lower_project_owner_name" error is raised on duplicate.
        """

        try:
            project = core_models.Project.objects.create(
                title="Project 1",
                workspace=self.workspace_1,
                category=self.ws_1_category_1,
            )
        except IntegrityError as e:
            self.assertRaises(IntegrityError)
            assert self.msg in str(e)

    def test_lower_name_workspace_fail_on_duplicate_during_update(self):
        """
        Test that project name is unique for a workspace at time of update.
        Check that "unique_lower_project_name_workspace" error is raised on duplicate.
        """

        msg = "unique_lower_project_name_workspace"
        self.cat_1_project_1.title = self.cat_1_project_2.title
        try:
            self.cat_1_project_1.full_clean()
        except ValidationError as e:
            self.assertRaises(ValidationError)
            assert self.msg in str(e)

    def test_unique_lower_name_workspace_allow_duplicate_for_different_category(self):
        """
        Check that duplicate name for different workspaces is allowed.
        """

        self.cat_1_project_1.title = "Unique"
        self.cat_1_project_1.save()
        self.cat_2_project_1.title = "Unique"
        self.cat_2_project_1.full_clean()
        self.cat_2_project_1.save()
        assert self.cat_2_project_1.title == "Unique"


class ProjectModelCleanSaveDeleteTests(ProjectModelFullSetupTestClass):
    """
    Test model's `clean`, `save`, `delete` methods
        - validation
        - functionality
    """


class ProjectModelTreeTests(ProjectModelFullSetupTestClass):
    """
    Test model's tree related
        - validation
        - functionality
    """

    @classmethod
    def db_create_categories_nested(cls, user, category):
        prefix = f'ws_{category.workspace.pk}_cat_{category.pk}_nested_project'
        setattr(cls,
                f'{prefix}_1',
                core_models.Project.objects.create(
                    title="Nested project 1",
                    workspace=category.workspace,
                    category=category,
                ))
        setattr(cls,
                f'{prefix}_1_1',
                core_models.Project.objects.create(
                    title="Nested project 1_1",
                    workspace=category.workspace,
                    category=category,
                    parent=getattr(cls, f'{prefix}_1'),
                ))
        setattr(cls,
                f'{prefix}_1_1_1',
                core_models.Project.objects.create(
                    title="Nested project 1_1_1",
                    workspace=category.workspace,
                    category=category,
                    parent=getattr(cls, f'{prefix}_1_1'),
                ))
        setattr(cls,
                f'{prefix}_1_1_2',
                core_models.Project.objects.create(
                    title="Nested project 1_1_2",
                    workspace=category.workspace,
                    category=category,
                    parent=getattr(cls, f'{prefix}_1_1'),
                ))

    @classmethod
    def setUpTestData(cls):
        """
        Create some nested categories in db.
        """
        super().setUpTestData()
        cls.db_create_categories_nested(cls.user, cls.ws_1_category_1)
        cls.db_create_categories_nested(cls.user, cls.ws_1_category_2)
        cls.db_create_categories_nested(cls.user, cls.ws_2_category_2)

    msg_parent = "Parent cannot be object itself."
    msg_parent_workspace = "Workspace should be same as parent's."
    msg_parent_category = "Category should be same as parent's."
    msg_visibility = "Visibility should be same as of parent's."

    def test_create(self):
        assert self.ws_1_cat_1_nested_project_1.title == "Nested project 1"

    def test_error_parent_same_on_update(self):
        """
        Test project parent is not same on update using patch.
        """

        self.ws_1_cat_1_nested_project_1_1.parent = self.ws_1_cat_1_nested_project_1_1
        try:
            self.ws_1_cat_1_nested_project_1_1.full_clean()
        except ValidationError as e:
            assert self.msg_parent in str(e)

    def test_error_parent_workspace_same_on_create(self):
        """
        Test project parent's workspace is same when creating.
        """

        try:
            core_models.Project.objects.create(
                title="project tmp",
                workspace=self.workspace_1,
                category=self.ws_1_category_1,
                parent=self.ws_2_cat_4_nested_project_1,
            )
        except ValidationError as e:
            assert self.msg_parent_workspace in str(e)

    def test_error_parent_workspace_same_on_update(self):
        """
        Test project parent's workspace is same when updating.
        """

        # ws_2_cat_4_nested_project_1: 4 is based on workspace provided in setup
        self.ws_1_cat_1_nested_project_1_1.parent = self.ws_2_cat_4_nested_project_1
        try:
            self.ws_1_cat_1_nested_project_1_1.full_clean()
        except ValidationError as e:
            assert self.msg_parent_workspace in str(e)

    def test_error_parent_category_same_on_create(self):
        """
        Test project parent's category is same when creating.
        """

        try:
            core_models.Project.objects.create(
                title="project tmp",
                workspace=self.workspace_1,
                category=self.ws_1_category_1,
                parent=self.ws_1_cat_2_nested_project_1,
            )
        except ValidationError as e:
            assert self.msg_parent_category in str(e)

    def test_error_parent_category_same_on_update(self):
        """
        Test project parent's category is same when updating.
        """

        # ws_1_cat_2_nested_project_1: 2 is based on category provided in setup
        self.ws_1_cat_1_nested_project_1_1.parent = self.ws_1_cat_2_nested_project_1
        try:
            self.ws_1_cat_1_nested_project_1_1.full_clean()
        except ValidationError as e:
            assert self.msg_parent_category in str(e)

    def test_visibility_same_as_parent_on_create(self):
        try:
            core_models.Project.objects.create(
                title="project tmp",
                workspace=self.ws_1_category_1.workspace,
                detail="",
                category=self.ws_1_category_1,
                parent=self.ws_1_cat_1_nested_project_1_1,
                is_visible=not self.ws_1_cat_1_nested_project_1_1.is_visible,
            )
        except ValidationError as e:
            assert self.msg_visibility in str(e)

    def test_visibility_same_as_parent_on_update(self):
        """
        Test project parent's visibility is same on update.
        """

        project = self.get_project_query(
            [self.ws_1_cat_1_nested_project_1_1.pk]).get()
        project.is_visible = False
        try:
            project.full_clean()
        except ValidationError as e:
            assert self.msg_visibility in str(e)
