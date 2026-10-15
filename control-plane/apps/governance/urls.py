from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AuditEventViewSet, ModelRegistryEntryViewSet, PromotionApprovalViewSet

router = DefaultRouter()
router.register(r"registry", ModelRegistryEntryViewSet, basename="registry")
router.register(r"approvals", PromotionApprovalViewSet, basename="approvals")
router.register(r"audit", AuditEventViewSet, basename="audit")

urlpatterns = [
    path("", include(router.urls)),
]
