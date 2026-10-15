import os

from rest_framework.permissions import BasePermission

from apps.organizations.models import TeamMembership


def is_service_request(request) -> bool:
    auth = getattr(request, "auth", None)
    payload = getattr(auth, "payload", None)
    if not isinstance(payload, dict):
        return False
    return payload.get("token_use") == "service"


def is_org_member(user, organization_id: int) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return TeamMembership.objects.filter(user=user, organization_id=organization_id).exists()


def is_org_admin(user, organization_id: int) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return TeamMembership.objects.filter(
        user=user,
        organization_id=organization_id,
        role=TeamMembership.ROLE_ADMIN,
    ).exists()


def can_request_approval(user, organization_id: int) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return TeamMembership.objects.filter(
        user=user,
        organization_id=organization_id,
        role__in=[TeamMembership.ROLE_ADMIN, TeamMembership.ROLE_ANALYST],
    ).exists()


class IsAuthenticatedOrServiceToken(BasePermission):
    def has_permission(self, request, view) -> bool:
        return is_service_request(request) or bool(request.user and request.user.is_authenticated)