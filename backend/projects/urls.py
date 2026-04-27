from rest_framework import routers
from django.urls import path, include
from .views import ProjectViewSet, TaskViewSet, ApplicationViewSet, UserViewSet, FileUploadViewSet

router = routers.DefaultRouter()
router.register(r'projects', ProjectViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'applications', ApplicationViewSet)
router.register(r'users', UserViewSet)
router.register(r'uploads', FileUploadViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
