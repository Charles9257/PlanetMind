from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import OrganizationViewSet, TeamMembershipViewSet

router = DefaultRouter()
router.register(r"memberships", TeamMembershipViewSet, basename="organization-memberships")
router.register(r"", OrganizationViewSet, basename="organizations")

urlpatterns = [
    path("", include(router.urls)),
]
