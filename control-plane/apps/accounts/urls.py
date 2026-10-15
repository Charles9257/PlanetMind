from django.urls import path

from .views import LoginView, MeView, RefreshView, ServiceTokenView

urlpatterns = [
    path("service-token", ServiceTokenView.as_view(), name="auth-service-token"),
    path("token", LoginView.as_view(), name="auth-token"),
    path("token/refresh", RefreshView.as_view(), name="auth-token-refresh"),
    path("me", MeView.as_view(), name="auth-me"),
]
