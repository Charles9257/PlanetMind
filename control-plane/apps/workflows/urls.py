from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import WorkflowRunViewSet

router = DefaultRouter()
router.register(r"runs", WorkflowRunViewSet, basename="workflow-runs")

urlpatterns = [
    path("", include(router.urls)),
]
