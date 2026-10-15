from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from apps.organizations.models import Organization, TeamMembership


class Command(BaseCommand):
    help = "Verify control-plane readiness for startup: secrets, org bootstrap, admin membership, and service user state"

    def handle(self, *args, **options):
        failures: list[str] = []
        checks: list[str] = []

        checks.append(self._check_secret("DJANGO_SECRET_KEY", settings.SECRET_KEY))
        checks.append(
            self._check_secret(
                "CONTROL_PLANE_SERVICE_CLIENT_SECRET",
                settings.CONTROL_PLANE_SERVICE_CLIENT_SECRET,
            )
        )
        checks.extend(self._check_secret_file("DJANGO_SECRET_KEY_FILE"))
        checks.extend(self._check_secret_file("CONTROL_PLANE_SERVICE_CLIENT_SECRET_FILE"))

        org_count = Organization.objects.count()
        if org_count == 0:
            failures.append("No organizations seeded. Run bootstrap_control_plane first.")
        else:
            checks.append(f"Organizations seeded: {org_count}")

        admin_memberships = TeamMembership.objects.filter(role=TeamMembership.ROLE_ADMIN).count()
        if admin_memberships == 0:
            failures.append("No organization admin memberships found.")
        else:
            checks.append(f"Organization admin memberships: {admin_memberships}")

        staff_admins = User.objects.filter(is_staff=True, is_active=True).count()
        if staff_admins == 0:
            failures.append("No active staff users available for governance administration.")
        else:
            checks.append(f"Active staff users: {staff_admins}")

        service_user_exists = User.objects.filter(username=settings.CONTROL_PLANE_SERVICE_USERNAME).exists()
        if not service_user_exists:
            failures.append(
                f"Service user '{settings.CONTROL_PLANE_SERVICE_USERNAME}' does not exist yet. Generate a service token or create it during setup."
            )
        else:
            checks.append(f"Service user present: {settings.CONTROL_PLANE_SERVICE_USERNAME}")

        self.stdout.write(self.style.NOTICE("Control-plane readiness checklist"))
        for item in checks:
            self.stdout.write(self.style.SUCCESS(f"[ok] {item}"))

        if failures:
            for item in failures:
                self.stdout.write(self.style.ERROR(f"[fail] {item}"))
            raise CommandError("Control-plane readiness check failed")

        self.stdout.write(self.style.SUCCESS("Control-plane readiness check passed"))

    def _check_secret(self, name: str, value: str | None) -> str:
        if not value or value in settings.PLACEHOLDER_SECRET_VALUES or len(value) < 32:
            raise CommandError(f"{name} is missing, placeholder, or shorter than 32 characters")
        return f"{name} configured"

    def _check_secret_file(self, env_name: str) -> list[str]:
        from os import getenv

        file_path = getenv(env_name)
        if not file_path:
            return []
        path = Path(file_path)
        if not path.exists():
            raise CommandError(f"{env_name} points to a missing file: {file_path}")
        return [f"{env_name} file exists"]