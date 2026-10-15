from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from apps.organizations.models import Organization, TeamMembership


class Command(BaseCommand):
    help = "Bootstrap the first organization and admin user with explicit secure values"

    def add_arguments(self, parser):
        parser.add_argument("--org-name", required=True)
        parser.add_argument("--org-slug", required=True)
        parser.add_argument("--admin-username", required=True)
        parser.add_argument("--admin-email", required=True)
        parser.add_argument("--admin-password", required=False)

    def handle(self, *args, **options):
        org_name = options["org_name"].strip()
        org_slug = options["org_slug"].strip()
        admin_username = options["admin_username"].strip()
        admin_email = options["admin_email"].strip()
        admin_password = options.get("admin_password") or None

        if admin_username.lower() in {"admin", "administrator", "test", "user"}:
            raise CommandError("Choose a non-default admin username")
        if not admin_password or len(admin_password) < 12:
            raise CommandError("Provide --admin-password with at least 12 characters")
        if admin_password.lower() in {"password", "changeme123!", "pass12345", "admin123456"}:
            raise CommandError("Choose a non-placeholder admin password")

        organization, _ = Organization.objects.get_or_create(name=org_name, slug=org_slug)
        admin_user, created = User.objects.get_or_create(
            username=admin_username,
            defaults={"email": admin_email, "is_active": True},
        )
        admin_user.email = admin_email
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.set_password(admin_password)
        admin_user.save()

        TeamMembership.objects.get_or_create(
            user=admin_user,
            organization=organization,
            defaults={"role": TeamMembership.ROLE_ADMIN},
        )

        service_user, _ = User.objects.get_or_create(
            username=settings.CONTROL_PLANE_SERVICE_USERNAME,
            defaults={"email": "service@planetmind.local", "is_active": True},
        )
        service_user.set_unusable_password()
        service_user.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Bootstrapped organization '{organization.slug}' with admin user '{admin_user.username}'"
            )
        )