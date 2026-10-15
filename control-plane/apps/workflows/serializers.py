from rest_framework import serializers

from .models import WorkflowRun


class WorkflowRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowRun
        fields = [
            "id",
            "workflow_name",
            "correlation_id",
            "status",
            "input_payload",
            "output_payload",
            "started_at",
            "finished_at",
        ]
