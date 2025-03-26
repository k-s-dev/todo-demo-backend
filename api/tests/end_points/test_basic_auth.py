from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


AUTH_ONLY_API_VIEWS = (
    "user",
    "workspace",
    "workspace-comment",
    "tag",
    "priority",
    "status",
    "category",
    "category-comment",
    "project",
    "project-comment",
    "task",
    "task-comment",
)


def create_user(username='user-1', password='testpass123'):
    """Create and return user."""
    return get_user_model().objects.create_user(username=username, password=password)


class PublicUsersApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_anonymous_access_denied(self):
        """Test auth is required for basic root and users view."""
        urls = ("/api/",)
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_logged_in_user_access_granted(self):
        """Test user is able to log in and access root api."""
        create_user()
        user_1 = get_user_model().objects.get(username="user-1")
        self.client.force_login(user=user_1)
        urls = ("/api/",)
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)


