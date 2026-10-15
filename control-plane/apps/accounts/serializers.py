from django.contrib.auth.models import User
from rest_framework import serializers


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class ServiceTokenRequestSerializer(serializers.Serializer):
    client_id = serializers.CharField(max_length=120)
    client_secret = serializers.CharField(max_length=255)
