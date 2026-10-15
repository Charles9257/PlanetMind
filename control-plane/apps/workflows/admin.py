from django.contrib import admin

from .models import WorkflowRun


@admin.register(WorkflowRun)
class WorkflowRunAdmin(admin.ModelAdmin):
    list_display = ("id", "workflow_name", "correlation_id", "status", "started_at", "finished_at")
    list_filter = ("workflow_name", "status")
