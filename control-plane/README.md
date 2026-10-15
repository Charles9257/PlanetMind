# PlanetMind Control Plane (Django)

This service provides control-plane capabilities for PlanetMind:
- Authentication and JWT issuance
- Organizations and role mapping
- Governance approvals and audit trail
- Workflow controls for model promotions

## Quick Start
1. Create and activate a Python virtual environment.
2. Install dependencies:
   pip install -r requirements.txt
3. Run migrations:
   python manage.py migrate
4. Bootstrap the first organization and admin user with explicit values:
   python manage.py bootstrap_control_plane --org-name "PlanetMind Org" --org-slug planetmind-org --admin-username orgadmin --admin-email orgadmin@example.com
5. Start server:
   python manage.py runserver 0.0.0.0:8100
6. Run readiness verification before deployment or startup automation:
   python manage.py check_control_plane_readiness

## Production Security
- Do not use placeholder secrets in production.
- Provide `DJANGO_SECRET_KEY` and `CONTROL_PLANE_SERVICE_CLIENT_SECRET` via environment variables or `*_FILE` secret mounts.
- When `DJANGO_DEBUG=false`, the control-plane fails fast if those secrets are missing, too short, or still set to placeholder values.
- `check_control_plane_readiness` also verifies seeded organizations, at least one org admin membership, at least one active staff user, and the service user expected by internal token issuance.
- Example managed-secret variables:
  - `DJANGO_SECRET_KEY_FILE=/run/secrets/control_plane_django_secret`
  - `CONTROL_PLANE_SERVICE_CLIENT_SECRET_FILE=/run/secrets/control_plane_service_client_secret`

## Base Paths
- Health: /control/health
- Auth: /control/auth
- Organizations: /control/orgs
- Governance: /control/governance
- Workflows: /control/workflows
