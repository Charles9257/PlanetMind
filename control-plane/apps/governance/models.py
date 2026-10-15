from django.conf import settings
from django.db import models

from apps.organizations.models import Organization


class ModelRegistryEntry(models.Model):
    SOURCE_FASTAPI = "fastapi"
    SOURCE_CHOICES = [
        (SOURCE_FASTAPI, "FastAPI"),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="model_registry_entries")
    source_system = models.CharField(max_length=40, choices=SOURCE_CHOICES, default=SOURCE_FASTAPI)
    external_model_run_id = models.PositiveIntegerField()
    module = models.CharField(max_length=80)
    model_name = models.CharField(max_length=120)
    model_version = models.CharField(max_length=80)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("source_system", "external_model_run_id"),)

    def __str__(self) -> str:
        return f"{self.source_system}:{self.external_model_run_id}:{self.module}"


class PromotionApproval(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    model_entry = models.ForeignKey(ModelRegistryEntry, on_delete=models.CASCADE, related_name="approvals")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="approval_requests")
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="approval_decisions",
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    decision_notes = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-requested_at",)

    def __str__(self) -> str:
        return f"approval:{self.model_entry_id}:{self.status}"


class AuditEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=120)
    entity_type = models.CharField(max_length=120)
    entity_id = models.CharField(max_length=120)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
