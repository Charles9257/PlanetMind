from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Organization, TeamMembership


class OrganizationSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Organization
        fields = ["id", "name", "slug", "created_at", "member_count"]


class TeamMembershipSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    input_username = serializers.CharField(write_only=True, required=False)
    input_email = serializers.EmailField(write_only=True, required=False)

    class Meta:
        model = TeamMembership
        fields = [
            "id",
            "user",
            "user_id",
            "username",
            "email",
            "organization",
            "organization_name",
            "role",
            "created_at",
            "input_username",
            "input_email",
        ]
        read_only_fields = ["user", "created_at"]

    def validate(self, attrs):
        if self.instance is None and "user" not in attrs:
            username = attrs.pop("input_username", None)
            email = attrs.pop("input_email", None)
            if not username:
                raise serializers.ValidationError({"input_username": "Existing username is required to assign membership"})
            try:
                attrs["user"] = User.objects.get(username=username)
            except User.DoesNotExist as exc:
                raise serializers.ValidationError({"input_username": "User not found"}) from exc
            if email and attrs["user"].email and attrs["user"].email != email:
                raise serializers.ValidationError({"input_email": "Email does not match existing user"})
        return attrs


class GovernanceUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "is_active"]
