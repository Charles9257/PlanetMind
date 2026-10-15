from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from apps.organizations.models import Organization, TeamMembership


class OrganizationsMembershipApiTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="PlanetMind Org", slug="planetmind-org")
        self.admin_user = User.objects.create_user(username="orgadmin", password="pass12345", email="orgadmin@example.com")
        self.member_user = User.objects.create_user(username="analyst", password="pass12345", email="analyst@example.com")
        TeamMembership.objects.create(user=self.admin_user, organization=self.org, role=TeamMembership.ROLE_ADMIN)

    def test_org_admin_can_create_membership(self):
        client = APIClient()
        client.force_authenticate(user=self.admin_user)
        response = client.post(
            "/control/orgs/memberships/",
            {"organization": self.org.id, "input_username": "analyst", "role": "member"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["username"], "analyst")

    def test_org_scope_limits_membership_visibility(self):
        other_org = Organization.objects.create(name="Other Org", slug="other-org")
        other_user = User.objects.create_user(username="otheradmin", password="pass12345")
        TeamMembership.objects.create(user=other_user, organization=other_org, role=TeamMembership.ROLE_ADMIN)
        TeamMembership.objects.create(user=self.member_user, organization=self.org, role=TeamMembership.ROLE_MEMBER)

        client = APIClient()
        client.force_authenticate(user=self.admin_user)
        response = client.get(f"/control/orgs/memberships/?organization={self.org.id}")
        self.assertEqual(response.status_code, 200)
        usernames = {row["username"] for row in response.json()["results"]}
        self.assertIn("orgadmin", usernames)
        self.assertIn("analyst", usernames)
        self.assertNotIn("otheradmin", usernames)

    def test_membership_list_returns_paginated_shape(self):
        TeamMembership.objects.create(user=self.member_user, organization=self.org, role=TeamMembership.ROLE_MEMBER)

        client = APIClient()
        client.force_authenticate(user=self.admin_user)
        response = client.get(f"/control/orgs/memberships/?organization={self.org.id}&page=1&page_size=1")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["page"], 1)
        self.assertEqual(payload["page_size"], 1)
        self.assertEqual(len(payload["results"]), 1)
