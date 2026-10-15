from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.governance.models import ModelRegistryEntry, PromotionApproval
from apps.organizations.models import Organization, TeamMembership


@override_settings(CONTROL_PLANE_API_TOKEN="")
class GovernanceApprovalFlowTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="PlanetMind Org", slug="planetmind-org")
        self.admin_user = User.objects.create_user(username="orgadmin", password="pass12345")
        self.approver_user = User.objects.create_user(username="approver", password="pass12345")
        self.analyst_user = User.objects.create_user(username="analyst", password="pass12345")
        self.member_user = User.objects.create_user(username="member", password="pass12345")
        TeamMembership.objects.create(user=self.admin_user, organization=self.org, role=TeamMembership.ROLE_ADMIN)
        TeamMembership.objects.create(user=self.approver_user, organization=self.org, role=TeamMembership.ROLE_ADMIN)
        TeamMembership.objects.create(user=self.analyst_user, organization=self.org, role=TeamMembership.ROLE_ANALYST)
        TeamMembership.objects.create(user=self.member_user, organization=self.org, role=TeamMembership.ROLE_MEMBER)

        self.model_entry = ModelRegistryEntry.objects.create(
            organization=self.org,
            source_system=ModelRegistryEntry.SOURCE_FASTAPI,
            external_model_run_id=101,
            module="climate",
            model_name="climate-risk-regressor",
            model_version="1",
            is_active=False,
        )

    def test_admin_can_request_and_approve_promotion(self):
        client = APIClient()
        client.force_authenticate(user=self.admin_user)

        create_response = client.post(
            "/control/governance/approvals/",
            {"model_entry": self.model_entry.id},
            format="json",
        )
        self.assertEqual(create_response.status_code, 201)
        approval_id = create_response.json()["id"]

        status_response = client.get(
            "/control/governance/approvals/status/",
            {"external_model_run_id": 101, "source_system": "fastapi"},
        )
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.json()["status"], "pending")
        self.assertFalse(status_response.json()["approved"])

        client.force_authenticate(user=self.approver_user)
        decide_response = client.post(
            f"/control/governance/approvals/{approval_id}/decide/",
            {"status": "approved", "decision_notes": "ready for production"},
            format="json",
        )
        self.assertEqual(decide_response.status_code, 200)
        self.assertEqual(decide_response.json()["status"], "approved")

        status_response = client.get(
            "/control/governance/approvals/status/",
            {"external_model_run_id": 101, "source_system": "fastapi"},
        )
        self.assertEqual(status_response.status_code, 200)
        self.assertTrue(status_response.json()["approved"])
        self.assertEqual(status_response.json()["model_entry_id"], self.model_entry.id)

    def test_analyst_can_request_approval(self):
        client = APIClient()
        client.force_authenticate(user=self.analyst_user)

        response = client.post(
            "/control/governance/approvals/",
            {"model_entry": self.model_entry.id},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "pending")

    def test_member_cannot_request_approval(self):
        client = APIClient()
        client.force_authenticate(user=self.member_user)

        response = client.post(
            "/control/governance/approvals/",
            {"model_entry": self.model_entry.id},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_requester_cannot_decide_own_request(self):
        client = APIClient()
        client.force_authenticate(user=self.admin_user)

        create_response = client.post(
            "/control/governance/approvals/",
            {"model_entry": self.model_entry.id},
            format="json",
        )
        self.assertEqual(create_response.status_code, 201)
        approval_id = create_response.json()["id"]

        self_decide = client.post(
            f"/control/governance/approvals/{approval_id}/decide/",
            {"status": "approved", "decision_notes": "self-approval attempt"},
            format="json",
        )
        self.assertEqual(self_decide.status_code, 403)
        self.assertIn("own", self_decide.json()["detail"].lower())

        client.force_authenticate(user=self.approver_user)
        other_decide = client.post(
            f"/control/governance/approvals/{approval_id}/decide/",
            {"status": "approved", "decision_notes": "independent review"},
            format="json",
        )
        self.assertEqual(other_decide.status_code, 200)
        self.assertEqual(other_decide.json()["status"], "approved")

    def test_member_cannot_decide_promotion(self):
        approval = PromotionApproval.objects.create(model_entry=self.model_entry, requested_by=self.admin_user)
        client = APIClient()
        client.force_authenticate(user=self.member_user)

        decide_response = client.post(
            f"/control/governance/approvals/{approval.id}/decide/",
            {"status": "approved", "decision_notes": "not allowed"},
            format="json",
        )

        self.assertEqual(decide_response.status_code, 403)

    def test_member_only_sees_org_scoped_approvals(self):
        other_org = Organization.objects.create(name="Other Org", slug="other-org")
        other_admin = User.objects.create_user(username="otheradmin", password="pass12345")
        TeamMembership.objects.create(user=other_admin, organization=other_org, role=TeamMembership.ROLE_ADMIN)
        other_entry = ModelRegistryEntry.objects.create(
            organization=other_org,
            source_system=ModelRegistryEntry.SOURCE_FASTAPI,
            external_model_run_id=202,
            module="climate",
            model_name="climate-risk-regressor",
            model_version="2",
            is_active=False,
        )
        PromotionApproval.objects.create(model_entry=self.model_entry, requested_by=self.admin_user)
        PromotionApproval.objects.create(model_entry=other_entry, requested_by=other_admin)

        client = APIClient()
        client.force_authenticate(user=self.member_user)
        response = client.get("/control/governance/approvals/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["model_entry_data"]["external_model_run_id"], 101)

    @override_settings(
        CONTROL_PLANE_SERVICE_CLIENT_ID="planetmind-backend",
        CONTROL_PLANE_SERVICE_CLIENT_SECRET="super-secret",
        CONTROL_PLANE_SERVICE_USERNAME="svc_planetmind_backend",
    )
    def test_service_token_can_sync_registry_and_create_pending_approval(self):
        token_client = APIClient()
        token_response = token_client.post(
            "/control/auth/service-token",
            {"client_id": "planetmind-backend", "client_secret": "super-secret"},
            format="json",
        )
        self.assertEqual(token_response.status_code, 200)
        access_token = token_response.json()["access"]

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = client.post(
            "/control/governance/registry/sync/",
            {
                "organization": self.org.id,
                "source_system": "fastapi",
                "external_model_run_id": 303,
                "module": "climate",
                "model_name": "climate-risk-regressor",
                "model_version": "3",
                "is_active": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["model_entry"]["external_model_run_id"], 303)
        self.assertEqual(response.json()["approval"]["status"], "pending")

        status_response = client.get(
            "/control/governance/approvals/status/",
            {"external_model_run_id": 303, "source_system": "fastapi"},
        )
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.json()["status"], "pending")

    def test_audit_list_returns_paginated_shape(self):
        client = APIClient()
        client.force_authenticate(user=self.admin_user)
        create_response = client.post(
            "/control/governance/approvals/",
            {"model_entry": self.model_entry.id},
            format="json",
        )
        self.assertEqual(create_response.status_code, 201)

        audit_response = client.get(
            "/control/governance/audit/?organization_id=%s&page=1&page_size=1" % self.org.id
        )
        self.assertEqual(audit_response.status_code, 200)
        payload = audit_response.json()
        self.assertGreaterEqual(payload["count"], 1)
        self.assertEqual(payload["page"], 1)
        self.assertEqual(payload["page_size"], 1)
        self.assertEqual(len(payload["results"]), 1)
