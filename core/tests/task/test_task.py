from django.core.exceptions import ValidationError
from django.db import IntegrityError
from core import models as core_models
from ..generic_classes import CustomTestCaseSetup


class TaskModelMinimalSetupClass(CustomTestCaseSetup):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def setUp(self):
        super().setUp()


class TaskModelFullSetupTestClass(TaskModelMinimalSetupClass):
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


class TaskModelAuthAndCrudTests(TaskModelFullSetupTestClass):
    """Test basic auth and CRUD operations on task view."""

    def test_task_create(self):
        """
        Test task create.
        """

        task = core_models.Task.objects.create(
            title="Task tmp",
            workspace=self.workspace_1,
            category=self.ws_1_category_1,
        )
        assert core_models.Task.objects.filter(title="Task tmp").exists()

    def test_task_read(self):
        """Test task read."""

        assert core_models.Task.objects.filter(
            title=self.cat_1_task_1.title).exists()

    def test_task_update(self):
        """Test task update."""

        self.cat_1_task_1.title = "random"
        self.cat_1_task_1.save(force_update=True)
        self.cat_1_task_1.refresh_from_db()
        assert self.cat_1_task_1.title == "random"

    def test_task_delete(self):
        """Test task delete."""

        self.cat_1_task_1.delete()
        task_1_query = self.get_task_query(pk_seq=[self.cat_1_task_1.pk])
        self.assertFalse(task_1_query.exists())


class TaskModelConstraintTests(TaskModelFullSetupTestClass):
    """
    Test model constraints.
    """

    msg = "unique_lower_task_title_category_workspace"

    def test_unique_lower_name_workspace_fail_on_duplicate_during_create(self):
        """
        Test that task name is unique for a workspace at time of creation.
        Check that "unique_lower_task_owner_name" error is raised on duplicate.
        """

        try:
            task = core_models.Task.objects.create(
                title="Task 1",
                workspace=self.workspace_1,
                category=self.ws_1_category_1,
            )
        except IntegrityError as e:
            self.assertRaises(IntegrityError)
            assert self.msg in str(e)

    def test_lower_name_workspace_fail_on_duplicate_during_update(self):
        """
        Test that task name is unique for a workspace at time of update.
        Check that "unique_lower_task_name_workspace" error is raised on duplicate.
        """

        msg = "unique_lower_task_name_workspace"
        self.cat_1_task_1.title = self.cat_1_task_2.title
        try:
            self.cat_1_task_1.full_clean()
        except ValidationError as e:
            self.assertRaises(ValidationError)
            assert self.msg in str(e)

    def test_unique_lower_name_workspace_allow_duplicate_for_different_category(self):
        """
        Check that duplicate name for different workspaces is allowed.
        """

        self.cat_1_task_1.title = "Unique"
        self.cat_1_task_1.save()
        self.cat_2_task_1.title = "Unique"
        self.cat_2_task_1.full_clean()
        self.cat_2_task_1.save()
        assert self.cat_2_task_1.title == "Unique"


class TaskModelCleanSaveDeleteTests(TaskModelFullSetupTestClass):
    """
    Test model's `clean`, `save`, `delete` methods
        - validation
        - functionality
    """


class TaskModelTreeTests(TaskModelFullSetupTestClass):
    """
    Test model's tree related
        - validation
        - functionality
    """

    @classmethod
    def db_create_categories_nested(cls, user, category):
        prefix = f'ws_{category.workspace.pk}_cat_{category.pk}_nested_task'
        setattr(cls,
                f'{prefix}_1',
                core_models.Task.objects.create(
                    title="Nested task 1",
                    workspace=category.workspace,
                    category=category,
                ))
        setattr(cls,
                f'{prefix}_1_1',
                core_models.Task.objects.create(
                    title="Nested task 1_1",
                    workspace=category.workspace,
                    category=category,
                    parent=getattr(cls, f'{prefix}_1'),
                ))
        setattr(cls,
                f'{prefix}_1_1_1',
                core_models.Task.objects.create(
                    title="Nested task 1_1_1",
                    workspace=category.workspace,
                    category=category,
                    parent=getattr(cls, f'{prefix}_1_1'),
                ))
        setattr(cls,
                f'{prefix}_1_1_2',
                core_models.Task.objects.create(
                    title="Nested task 1_1_2",
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
        assert self.ws_1_cat_1_nested_task_1.title == "Nested task 1"

    def test_error_parent_same_on_update(self):
        """
        Test task parent is not same on update using patch.
        """

        self.ws_1_cat_1_nested_task_1_1.parent = self.ws_1_cat_1_nested_task_1_1
        try:
            self.ws_1_cat_1_nested_task_1_1.full_clean()
        except ValidationError as e:
            assert self.msg_parent in str(e)

    def test_error_parent_workspace_same_on_create(self):
        """
        Test task parent's workspace is same when creating.
        """

        try:
            core_models.Task.objects.create(
                title="task tmp",
                workspace=self.workspace_1,
                category=self.ws_1_category_1,
                parent=self.ws_2_cat_4_nested_task_1,
            )
        except ValidationError as e:
            assert self.msg_parent_workspace in str(e)

    def test_error_parent_workspace_same_on_update(self):
        """
        Test task parent's workspace is same when updating.
        """

        # ws_2_cat_4_nested_task_1: 4 is based on workspace provided in setup
        self.ws_1_cat_1_nested_task_1_1.parent = self.ws_2_cat_4_nested_task_1
        try:
            self.ws_1_cat_1_nested_task_1_1.full_clean()
        except ValidationError as e:
            assert self.msg_parent_workspace in str(e)

    def test_error_parent_category_same_on_create(self):
        """
        Test task parent's category is same when creating.
        """

        try:
            core_models.Task.objects.create(
                title="task tmp",
                workspace=self.workspace_1,
                category=self.ws_1_category_1,
                parent=self.ws_1_cat_2_nested_task_1,
            )
        except ValidationError as e:
            assert self.msg_parent_category in str(e)

    def test_error_parent_category_same_on_update(self):
        """
        Test task parent's category is same when updating.
        """

        # ws_1_cat_2_nested_task_1: 2 is based on category provided in setup
        self.ws_1_cat_1_nested_task_1_1.parent = self.ws_1_cat_2_nested_task_1
        try:
            self.ws_1_cat_1_nested_task_1_1.full_clean()
        except ValidationError as e:
            assert self.msg_parent_category in str(e)

    def test_visibility_same_as_parent_on_create(self):
        try:
            core_models.Task.objects.create(
                title="task tmp",
                workspace=self.ws_1_category_1.workspace,
                detail="",
                category=self.ws_1_category_1,
                parent=self.ws_1_cat_1_nested_task_1_1,
                is_visible=not self.ws_1_cat_1_nested_task_1_1.is_visible,
            )
        except ValidationError as e:
            assert self.msg_visibility in str(e)

    def test_visibility_same_as_parent_on_update(self):
        """
        Test task parent's visibility is same on update.
        """

        task = self.get_task_query(
            [self.ws_1_cat_1_nested_task_1_1.pk]).get()
        task.is_visible = False
        try:
            task.full_clean()
        except ValidationError as e:
            assert self.msg_visibility in str(e)
