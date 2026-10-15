# Django + FastAPI Migration Implementation Checklist

This checklist operationalizes the migration blueprint into executable tickets.

## Ticket ID Convention
- Epic IDs: PM-DJ-E01, PM-DJ-E02, PM-DJ-E03
- Story/Task IDs: PM-DJ-101+

## Epic PM-DJ-E01: Control Plane Foundation and Identity
Goal: Stand up Django control plane and deliver authentication, organizations, and RBAC.

### PM-DJ-101 Bootstrap Django control-plane service
- [ ] Create control-plane project layout and settings package
- [ ] Add Django + DRF + JWT dependencies
- [ ] Add app registration skeleton for accounts, organizations, governance, workflows
- [ ] Verify server starts with sqlite default config
Acceptance criteria:
- manage.py runserver starts without import errors
- /control/health endpoint returns 200
Estimate: 3 points
Owner: Platform

### PM-DJ-102 Configure environment and settings profiles
- [ ] Add .env driven settings for SECRET_KEY, DEBUG, ALLOWED_HOSTS, DB
- [ ] Add local sqlite fallback and PostgreSQL override support
- [ ] Add CORS + REST framework defaults
Acceptance criteria:
- Environment variable matrix documented and validated in startup
- Local boot works with no manual code edits
Estimate: 3 points
Owner: Platform

### PM-DJ-103 Implement accounts app (auth + JWT)
- [ ] Create user profile model extension strategy
- [ ] Add login/token endpoints using SimpleJWT
- [ ] Add user summary endpoint
Acceptance criteria:
- Token issue/refresh works
- Authenticated endpoint validates token claims
Estimate: 5 points
Owner: Backend

### PM-DJ-104 Implement organizations and team membership
- [ ] Add Organization model
- [ ] Add TeamMembership model (user, org, role)
- [ ] Add CRUD/list endpoints for organizations
Acceptance criteria:
- Users can be linked to org with role
- Organization list is scoped to authenticated user
Estimate: 5 points
Owner: Backend

### PM-DJ-105 Implement RBAC permission checks
- [ ] Add role constants and permission helpers
- [ ] Add DRF permission classes for control-plane APIs
- [ ] Add object-level ownership checks
Acceptance criteria:
- Non-privileged users cannot access admin actions
- Permission tests pass for member/admin roles
Estimate: 5 points
Owner: Backend

## Epic PM-DJ-E02: Governance and Workflow Controls
Goal: Deliver model approval, promotion governance, and auditable workflow records in Django.

### PM-DJ-106 Create governance domain models
- [ ] Add ModelRegistryEntry model
- [ ] Add PromotionApproval model
- [ ] Add AuditEvent model
Acceptance criteria:
- Django migrations create governance tables
- Admin shows all three models
Estimate: 5 points
Owner: Backend

### PM-DJ-107 Build governance API endpoints
- [ ] Add endpoints for approval request, approve, reject, and status
- [ ] Add endpoint to fetch audit timeline by model/version
- [ ] Add endpoint to fetch pending approvals queue
Acceptance criteria:
- Approval state transitions enforce valid workflow
- Audit timeline reflects all transitions
Estimate: 8 points
Owner: Backend

### PM-DJ-108 Add workflow engine baseline
- [ ] Add workflow state machine service for promotion lifecycle
- [ ] Add guardrails for required approver roles
- [ ] Add idempotency key handling for approval actions
Acceptance criteria:
- Duplicate actions do not create duplicate transitions
- Invalid transitions return consistent error format
Estimate: 8 points
Owner: Backend

### PM-DJ-109 Integrate governance gate into FastAPI promotion flow
- [ ] Update FastAPI promotion route to call Django approval status endpoint
- [ ] Block promotion when approval state is not APPROVED
- [ ] Persist correlation ID for cross-service tracing
Acceptance criteria:
- Promotion is blocked until governance approval exists
- Correlation ID is present in Django and FastAPI logs
Estimate: 8 points
Owner: Backend

## Epic PM-DJ-E03: Hybrid Integration, UI Wiring, and Delivery Hardening
Goal: Connect frontend and FastAPI to control plane, then validate end-to-end operations.

### PM-DJ-110 Add service-to-service auth between Django and FastAPI
- [ ] Standardize JWT issuer and audience
- [ ] Add FastAPI middleware claim validation for control-plane tokens
- [ ] Add service principal token flow for backend-to-backend calls
Acceptance criteria:
- FastAPI rejects invalid issuer/audience
- Valid control-plane token accepted across protected endpoints
Estimate: 5 points
Owner: Platform

### PM-DJ-111 Update frontend API routing for control endpoints
- [ ] Split frontend API client into intelligence and control clients
- [ ] Route governance UI actions to Django /control/governance endpoints
- [ ] Preserve existing climate/risk flows in FastAPI paths
Acceptance criteria:
- Existing climate and risk UI flows remain functional
- Governance UI reads/writes via control-plane endpoints
Estimate: 5 points
Owner: Frontend

### PM-DJ-112 Add control-plane operations views
- [ ] Add approvals queue view
- [ ] Add model audit trail view
- [ ] Add RBAC role management view
Acceptance criteria:
- Operations user can process approval lifecycle from UI
- Audit trail page supports filtering by module/model/version
Estimate: 8 points
Owner: Frontend

### PM-DJ-113 Add tests for control plane and hybrid contracts
- [ ] Add Django unit/integration tests for auth/org/governance/workflow APIs
- [ ] Add FastAPI tests for governance-gated promotion route
- [ ] Add frontend tests for mixed control/intelligence API routing
Acceptance criteria:
- Test suites pass in CI for both services
- Negative-path tests cover unauthorized and invalid transition cases
Estimate: 8 points
Owner: QA

### PM-DJ-114 Add deployment and local-run docs for dual-service model
- [ ] Document local run sequence for Django + FastAPI + frontend
- [ ] Document env vars and troubleshooting matrix
- [ ] Add migration order documentation (Django migrations then Alembic as applicable)
Acceptance criteria:
- New contributor can boot stack from docs in under 30 minutes
- Health checks for both services documented and validated
Estimate: 3 points
Owner: Platform

## Dependency Order
1. PM-DJ-101
2. PM-DJ-102
3. PM-DJ-103 + PM-DJ-104
4. PM-DJ-105
5. PM-DJ-106
6. PM-DJ-107
7. PM-DJ-108
8. PM-DJ-109
9. PM-DJ-110
10. PM-DJ-111 + PM-DJ-112
11. PM-DJ-113
12. PM-DJ-114

## Definition of Done (Migration Stream)
- Django control-plane service is running and versioned with migrations.
- FastAPI promotion path enforces governance approvals from Django.
- Frontend uses split API routing and supports governance workflows.
- Tests and docs cover the dual-service operating model.
