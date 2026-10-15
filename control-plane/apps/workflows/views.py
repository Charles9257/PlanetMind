from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .models import WorkflowRun
from .serializers import WorkflowRunSerializer


class WorkflowRunViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = WorkflowRunSerializer
    queryset = WorkflowRun.objects.all().order_by("-started_at")
