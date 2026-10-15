from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.organizations.models import Organization, TeamMembership


@override_settings(
    CONTROL_PLANE_SERVICE_CLIENT_ID="planetmind-backend",
    CONTROL_PLANE_SERVICE_CLIENT_SECRET="super-secret",
    CONTROL_PLANE_SERVICE_USERNAME="svc_planetmind_backend",
)
class AccountsServiceTokenTest(TestCase):
    def test_service_token_issue(self):
        client = APIClient()
        response = client.post(
            "/control/auth/service-token",
            {"client_id": "planetmind-backend", "client_secret": "super-secret"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["token_type"], "Bearer")
        self.assertEqual(response.json()["audience"], "planetmind-internal-services")

    def test_service_token_rejects_invalid_credentials(self):
        client = APIClient()
        response = client.post(
            "/control/auth/service-token",
            {"client_id": "planetmind-backend", "client_secret": "wrong"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)


@override_settings(
    SECRET_KEY="12345678901234567890123456789012",
    CONTROL_PLANE_SERVICE_CLIENT_SECRET="abcdefghijklmnopqrstuvwxyz123456",
    CONTROL_PLANE_SERVICE_USERNAME="svc_planetmind_backend",
)
class ControlPlaneReadinessCommandTest(TestCase):
    def test_readiness_command_passes_with_seeded_state(self):
        org = Organization.objects.create(name="PlanetMind Org", slug="planetmind-org")
        admin_user = User.objects.create_user(username="orgadmin", password="strongpass12345", is_staff=True)
        TeamMembership.objects.create(user=admin_user, organization=org, role=TeamMembership.ROLE_ADMIN)
        service_user = User.objects.create_user(username="svc_planetmind_backend")
        service_user.set_unusable_password()
        service_user.save()

        stdout = StringIO()
        call_command("check_control_plane_readiness", stdout=stdout)
        self.assertIn("Control-plane readiness check passed", stdout.getvalue())

    def test_readiness_command_fails_without_seed_data(self):
        with self.assertRaises(CommandError):
            call_command("check_control_plane_readiness")
