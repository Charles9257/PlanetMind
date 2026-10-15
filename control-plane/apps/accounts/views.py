from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import ServiceTokenRequestSerializer, UserSummarySerializer


class LoginView(TokenObtainPairView):
    pass


class RefreshView(TokenRefreshView):
    pass


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSummarySerializer(request.user)
        return Response(serializer.data)


class ServiceTokenView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = ServiceTokenRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data["client_id"] != settings.CONTROL_PLANE_SERVICE_CLIENT_ID:
            return Response({"detail": "Invalid service credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        if serializer.validated_data["client_secret"] != settings.CONTROL_PLANE_SERVICE_CLIENT_SECRET:
            return Response({"detail": "Invalid service credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        service_user, _ = User.objects.get_or_create(
            username=settings.CONTROL_PLANE_SERVICE_USERNAME,
            defaults={"is_active": True, "email": "service@planetmind.local"},
        )
        service_user.set_unusable_password()
        service_user.save(update_fields=["password"])

        token = AccessToken.for_user(service_user)
        token["token_use"] = "service"
        token["scope"] = "governance:read governance:write registry:sync"
        token["client_id"] = settings.CONTROL_PLANE_SERVICE_CLIENT_ID

        return Response(
            {
                "access": str(token),
                "token_type": "Bearer",
                "issuer": settings.CONTROL_PLANE_JWT_ISSUER,
                "audience": settings.CONTROL_PLANE_JWT_AUDIENCE,
                "scope": token["scope"],
            }
        )
