from rest_framework import serializers

from .models import AuditEvent, ModelRegistryEntry, PromotionApproval


class ModelRegistryEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelRegistryEntry
        fields = [
            "id",
            "organization",
            "source_system",
            "external_model_run_id",
            "module",
            "model_name",
            "model_version",
            "is_active",
            "created_at",
        ]


class PromotionApprovalSerializer(serializers.ModelSerializer):
    model_entry_data = ModelRegistryEntrySerializer(source="model_entry", read_only=True)

    class Meta:
        model = PromotionApproval
        fields = [
            "id",
            "model_entry",
            "model_entry_data",
            "requested_by",
            "decided_by",
            "status",
            "decision_notes",
            "requested_at",
            "decided_at",
        ]
        read_only_fields = ["requested_by", "decided_by", "status", "requested_at", "decided_at"]


class ApprovalDecisionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[PromotionApproval.STATUS_APPROVED, PromotionApproval.STATUS_REJECTED]
    )
    decision_notes = serializers.CharField(allow_blank=True, required=False, default="")


class ApprovalStatusSerializer(serializers.Serializer):
    approved = serializers.BooleanField()
    status = serializers.CharField()
    source_system = serializers.CharField()
    external_model_run_id = serializers.IntegerField()
    approval_id = serializers.IntegerField(allow_null=True)
    model_entry_id = serializers.IntegerField(allow_null=True)
    organization_id = serializers.IntegerField(allow_null=True)


class AuditEventSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source="actor.username", read_only=True)

    class Meta:
        model = AuditEvent
        fields = ["id", "actor", "actor_username", "event_type", "entity_type", "entity_id", "payload", "created_at"]
