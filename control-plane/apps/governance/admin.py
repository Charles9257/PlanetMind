from django.contrib import admin

from .models import AuditEvent, ModelRegistryEntry, PromotionApproval


@admin.register(ModelRegistryEntry)
class ModelRegistryEntryAdmin(admin.ModelAdmin):
    list_display = ("id", "module", "model_name", "model_version", "is_active", "created_at")
    list_filter = ("module", "is_active")


@admin.register(PromotionApproval)
class PromotionApprovalAdmin(admin.ModelAdmin):
    list_display = ("id", "model_entry", "status", "requested_by", "decided_by", "requested_at", "decided_at")
    list_filter = ("status",)


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("id", "event_type", "entity_type", "entity_id", "actor", "created_at")
    list_filter = ("event_type", "entity_type")
