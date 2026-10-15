from django.contrib import admin
from django.http import HttpResponse, JsonResponse
from django.urls import include, path


def health_view(request):
    return JsonResponse({"status": "ok", "service": "control-plane"})


def root_status_view(request):
    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PlanetMind Control Plane</title>
  <style>
    body { margin: 0; min-height: 100vh; display: grid; place-items: center;
           font-family: "Segoe UI", sans-serif; background: #f2f6fd; color: #142033; }
    .card { background: #fff; border: 1px solid #d7e2f5; border-radius: 16px;
            padding: 2rem 2.5rem; box-shadow: 0 10px 30px rgba(11,42,92,.08); max-width: 520px; }
    .status { display: inline-flex; align-items: center; gap: .5rem; font-weight: 700;
              color: #17633d; background: #ddf5e8; border-radius: 999px; padding: .35rem .9rem; }
    .dot { width: 10px; height: 10px; border-radius: 50%; background: #22a06b; }
    a { color: #125ecf; font-weight: 600; text-decoration: none; }
    ul { padding-left: 1.1rem; line-height: 2; }
  </style>
</head>
<body>
  <div class="card">
    <p><span class="status"><span class="dot"></span> PlanetMind Control Plane is running</span></p>
    <p>Django governance plane &middot; auth, organizations, approvals, audit</p>
    <ul>
      <li><a href="/control/health">Health check</a> &mdash; /control/health</li>
      <li><a href="/admin/">Django admin</a> &mdash; /admin/</li>
      <li><a href="/metrics">Prometheus metrics</a> &mdash; /metrics</li>
      <li><a href="http://localhost:5173">Frontend app</a> &mdash; http://localhost:5173</li>
      <li><a href="http://localhost:8000">Backend API</a> &mdash; http://localhost:8000</li>
    </ul>
  </div>
</body>
</html>"""
    return HttpResponse(html)


urlpatterns = [
    path("", root_status_view, name="root-status"),
    path("admin/", admin.site.urls),
    path("control/health", health_view, name="control-health"),
    path("control/auth/", include("apps.accounts.urls")),
    path("control/orgs/", include("apps.organizations.urls")),
    path("control/governance/", include("apps.governance.urls")),
    path("control/workflows/", include("apps.workflows.urls")),
    path("", include("django_prometheus.urls")),
]
