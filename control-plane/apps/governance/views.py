from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import AuditEvent, ModelRegistryEntry, PromotionApproval
from .permissions import IsAuthenticatedOrServiceToken, can_request_approval, is_org_admin, is_service_request
from .serializers import (
    ApprovalDecisionSerializer,
    ApprovalStatusSerializer,
    AuditEventSerializer,
    ModelRegistryEntrySerializer,
    PromotionApprovalSerializer,
)


class ModelRegistryEntryViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ModelRegistryEntrySerializer

    def get_queryset(self):
        queryset = ModelRegistryEntry.objects.all().order_by("-created_at")
        user = self.request.user
        if user.is_superuser:
            return queryset
        return queryset.filter(organization__memberships__user=user).distinct()

    def perform_create(self, serializer):
        organization_id = serializer.validated_data["organization"].id
        if is_service_request(self.request):
            serializer.save()
            return
        if not is_org_admin(self.request.user, organization_id):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Organization admin role required")
        serializer.save()

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticatedOrServiceToken], url_path="sync")
    def sync(self, request):
        serializer = ModelRegistryEntrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        model_entry, created = ModelRegistryEntry.objects.update_or_create(
            source_system=data["source_system"],
            external_model_run_id=data["external_model_run_id"],
            defaults={
                "organization": data["organization"],
                "module": data["module"],
                "model_name": data["model_name"],
                "model_version": data["model_version"],
                "is_active": data["is_active"],
            },
        )

        approval = model_entry.approvals.order_by("-requested_at").first()
        if approval is None or approval.status != PromotionApproval.STATUS_PENDING:
            actor = request.user if request.user and request.user.is_authenticated else None
            approval = PromotionApproval.objects.create(model_entry=model_entry, requested_by=actor or User.objects.get(username=settings.CONTROL_PLANE_SERVICE_USERNAME))
            AuditEvent.objects.create(
                actor=actor,
                event_type="promotion_approval_requested",
                entity_type="promotion_approval",
                entity_id=str(approval.id),
                payload={
                    "model_entry_id": model_entry.id,
                    "external_model_run_id": model_entry.external_model_run_id,
                    "organization_id": model_entry.organization_id,
                    "created_by_sync": True,
                },
            )

        return Response(
            {
                "created": created,
                "model_entry": ModelRegistryEntrySerializer(model_entry).data,
                "approval": PromotionApprovalSerializer(approval).data,
            },
            status=status.HTTP_200_OK,
        )


class PromotionApprovalViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedOrServiceToken]
    serializer_class = PromotionApprovalSerializer

    def get_queryset(self):
        queryset = PromotionApproval.objects.select_related("model_entry", "requested_by", "decided_by").all()

        external_model_run_id = self.request.query_params.get("external_model_run_id")
        source_system = self.request.query_params.get("source_system")
        status_filter = self.request.query_params.get("status")
        module = self.request.query_params.get("module")

        if external_model_run_id:
            queryset = queryset.filter(model_entry__external_model_run_id=external_model_run_id)
        if source_system:
            queryset = queryset.filter(model_entry__source_system=source_system)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if module:
            queryset = queryset.filter(model_entry__module=module)

        if self.request.user and self.request.user.is_authenticated:
            if self.request.user.is_superuser:
                return queryset
            return queryset.filter(model_entry__organization__memberships__user=self.request.user).distinct()

        if is_service_request(self.request):
            return queryset
        return queryset.none()

    def perform_create(self, serializer):
        model_entry = serializer.validated_data["model_entry"]
        if is_service_request(self.request):
            serializer.save(requested_by=self.request.user, status=PromotionApproval.STATUS_PENDING)
            return
        if not can_request_approval(self.request.user, model_entry.organization_id):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Organization admin or analyst role required to request approval")

        approval = serializer.save(requested_by=self.request.user, status=PromotionApproval.STATUS_PENDING)
        AuditEvent.objects.create(
            actor=self.request.user,
            event_type="promotion_approval_requested",
            entity_type="promotion_approval",
            entity_id=str(approval.id),
            payload={
                "model_entry_id": model_entry.id,
                "external_model_run_id": model_entry.external_model_run_id,
                "organization_id": model_entry.organization_id,
            },
        )

    @action(detail=False, methods=["get"], url_path="status")
    def status_view(self, request):
        source_system = request.query_params.get("source_system", ModelRegistryEntry.SOURCE_FASTAPI)
        external_model_run_id = request.query_params.get("external_model_run_id")
        if not external_model_run_id:
            return Response({"detail": "external_model_run_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        model_entry = ModelRegistryEntry.objects.filter(
            source_system=source_system,
            external_model_run_id=external_model_run_id,
        ).first()
        if model_entry is None:
            payload = {
                "approved": False,
                "status": "missing",
                "source_system": source_system,
                "external_model_run_id": int(external_model_run_id),
                "approval_id": None,
                "model_entry_id": None,
                "organization_id": None,
            }
            return Response(ApprovalStatusSerializer(payload).data)

        if is_service_request(request):
            pass
        elif request.user and request.user.is_authenticated and not request.user.is_superuser:
            if not model_entry.organization.memberships.filter(user=request.user).exists():
                return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        approval = model_entry.approvals.order_by("-requested_at").first()
        approval_status = approval.status if approval else "missing"
        payload = {
            "approved": approval_status == PromotionApproval.STATUS_APPROVED,
            "status": approval_status,
            "source_system": source_system,
            "external_model_run_id": model_entry.external_model_run_id,
            "approval_id": approval.id if approval else None,
            "model_entry_id": model_entry.id,
            "organization_id": model_entry.organization_id,
        }
        return Response(ApprovalStatusSerializer(payload).data)

    @action(detail=True, methods=["post"], url_path="decide")
    def decide(self, request, pk=None):
        approval = self.get_object()
        if not request.user or not request.user.is_authenticated:
            return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        if not is_org_admin(request.user, approval.model_entry.organization_id):
            return Response({"detail": "Organization admin role required"}, status=status.HTTP_403_FORBIDDEN)
        if approval.requested_by_id == request.user.id:
            return Response(
                {"detail": "Approvers cannot decide their own approval requests"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if approval.status != PromotionApproval.STATUS_PENDING:
            return Response({"detail": "Only pending approvals can transition"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ApprovalDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        approval.status = serializer.validated_data["status"]
        approval.decision_notes = serializer.validated_data["decision_notes"]
        approval.decided_by = request.user
        approval.decided_at = timezone.now()
        approval.save(update_fields=["status", "decision_notes", "decided_by", "decided_at"])

        AuditEvent.objects.create(
            actor=request.user,
            event_type=f"promotion_approval_{approval.status}",
            entity_type="promotion_approval",
            entity_id=str(approval.id),
            payload={
                "model_entry_id": approval.model_entry_id,
                "external_model_run_id": approval.model_entry.external_model_run_id,
                "organization_id": approval.model_entry.organization_id,
            },
        )

        return Response(PromotionApprovalSerializer(approval).data)


class AuditEventViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AuditEventSerializer

    def get_queryset(self):
        queryset = AuditEvent.objects.all().order_by("-created_at")
        event_type = self.request.query_params.get("event_type")
        entity_type = self.request.query_params.get("entity_type")
        organization_id = self.request.query_params.get("organization_id")
        external_model_run_id = self.request.query_params.get("external_model_run_id")
        actor_username = self.request.query_params.get("actor_username")

        if event_type:
            queryset = queryset.filter(event_type=event_type)
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
        if organization_id:
            # payload values are stored as JSON ints; query params arrive as strings, and
            # SQLite's JSON1 comparisons are type-strict, so cast before filtering.
            queryset = queryset.filter(payload__organization_id=int(organization_id))
        if external_model_run_id:
            queryset = queryset.filter(payload__external_model_run_id=int(external_model_run_id))
        if actor_username:
            queryset = queryset.filter(actor__username__icontains=actor_username)

        user = self.request.user
        if is_service_request(self.request):
            return queryset
        if user.is_superuser:
            return queryset
        organization_ids = user.teammembership_set.values_list("organization_id", flat=True)
        return queryset.filter(payload__organization_id__in=organization_ids)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = max(1, int(request.query_params.get("page", 1)))
        page_size = min(100, max(1, int(request.query_params.get("page_size", 10))))
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
