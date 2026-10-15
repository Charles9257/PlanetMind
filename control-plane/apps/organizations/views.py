from django.contrib.auth.models import User
from django.db.models import Count
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Organization, TeamMembership
from .serializers import GovernanceUserSerializer, OrganizationSerializer, TeamMembershipSerializer


def _is_org_admin(user, organization_id: int) -> bool:
    if user.is_superuser:
        return True
    return TeamMembership.objects.filter(
        user=user,
        organization_id=organization_id,
        role=TeamMembership.ROLE_ADMIN,
    ).exists()


class OrganizationViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        queryset = Organization.objects.annotate(member_count=Count("memberships", distinct=True)).order_by("name")
        user = self.request.user
        if user.is_superuser:
            return queryset
        return queryset.filter(memberships__user=user).distinct()

    @action(detail=False, methods=["get"], url_path="users")
    def users(self, request):
        queryset = User.objects.filter(is_active=True).order_by("username")
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(username__icontains=search) | queryset.filter(email__icontains=search)
        serializer = GovernanceUserSerializer(queryset.distinct()[:50], many=True)
        return Response(serializer.data)


class TeamMembershipViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TeamMembershipSerializer

    def get_queryset(self):
        queryset = TeamMembership.objects.select_related("user", "organization").order_by("organization__name", "user__username")
        organization_id = self.request.query_params.get("organization")
        role = self.request.query_params.get("role")
        username = self.request.query_params.get("username")
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        if role:
            queryset = queryset.filter(role=role)
        if username:
            queryset = queryset.filter(user__username__icontains=username)

        user = self.request.user
        if user.is_superuser:
            return queryset
        return queryset.filter(organization__memberships__user=user).distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = max(1, int(request.query_params.get("page", 1)))
        page_size = min(50, max(1, int(request.query_params.get("page_size", 10))))
        total = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        serializer = self.get_serializer(queryset[start:end], many=True)
        return Response(
            {
                "count": total,
                "page": page,
                "page_size": page_size,
                "results": serializer.data,
            }
        )

    def perform_create(self, serializer):
        organization_id = serializer.validated_data["organization"].id
        if not _is_org_admin(self.request.user, organization_id):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Organization admin role required")
        serializer.save()

    def perform_update(self, serializer):
        organization_id = serializer.instance.organization_id
        if not _is_org_admin(self.request.user, organization_id):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Organization admin role required")
        serializer.save()

    def perform_destroy(self, instance):
        if not _is_org_admin(self.request.user, instance.organization_id):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Organization admin role required")
        instance.delete()
