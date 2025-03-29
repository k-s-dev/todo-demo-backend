from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from . import views

app_name = 'api'


router = DefaultRouter(use_regex_path=False)
router.register('user/<str:user_id>/workspace', views.WorkspaceViewSet,
                basename='workspace')

# user endpoints
router.register('user/<str:user_id>/category', views.CategoryViewSet,
                basename='user-category')
router.register('user/<str:user_id>/priority', views.PriorityViewSet,
                basename='user-priority')
router.register('user/<str:user_id>/status', views.StatusViewSet,
                basename='user-status')
router.register('user/<str:user_id>/tag', views.TagViewSet,
                basename='user-tag')
router.register('user/<str:user_id>/project', views.ProjectViewSet,
                basename='user-project')
router.register('user/<str:user_id>/task', views.TaskViewSet,
                basename='user-task')


urlpatterns = [
    path('', include(router.urls)),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api:schema'),
         name='docs'),
]
