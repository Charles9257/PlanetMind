from django.db import models


class WorkflowRun(models.Model):
    workflow_name = models.CharField(max_length=120)
    correlation_id = models.CharField(max_length=120, db_index=True)
    status = models.CharField(max_length=40, default="pending")
    input_payload = models.JSONField(default=dict)
    output_payload = models.JSONField(default=dict)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.workflow_name}:{self.correlation_id}:{self.status}"
