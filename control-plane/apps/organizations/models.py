from django.conf import settings
from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=180, unique=True)
    slug = models.SlugField(max_length=180, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class TeamMembership(models.Model):
    ROLE_VIEWER = "viewer"
    ROLE_MEMBER = "member"
    ROLE_ANALYST = "analyst"
    ROLE_ADMIN = "admin"
    ROLE_CHOICES = [
        (ROLE_VIEWER, "Viewer"),
        (ROLE_MEMBER, "Member"),
        (ROLE_ANALYST, "Analyst"),
        (ROLE_ADMIN, "Admin"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "organization")

    def __str__(self) -> str:
        return f"{self.user_id}:{self.organization_id}:{self.role}"
