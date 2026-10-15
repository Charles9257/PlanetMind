# PlanetMind Django + FastAPI Migration Blueprint

## Objective
Adopt a hybrid architecture where Django becomes the control plane and FastAPI remains the intelligence plane, without breaking current MVP delivery momentum.

## Target Architecture
### Django (Control Plane)
- Users, organizations, and role-based permissions
- Governance workflows: model approvals, promotion controls, audit records
- Business workflow orchestration and policy controls
- Reporting dashboards, admin operations, and operational metadata

### FastAPI (Intelligence Plane)
- Domain prediction and simulation APIs
- Model training, model lifecycle, and inference orchestration
- Explainability payload generation and analytics endpoints
- Performance-sensitive AI/ML and async processing paths

## Current Repo Baseline (What Exists Today)
### FastAPI assets already in place
- API contracts and routes: backend/app/api/routes.py
- Domain and climate request/response schemas: backend/app/models.py
- Climate model lifecycle service: backend/app/services/climate_analytics.py
- Risk scoring and simulation service: backend/app/services/risk_engine.py
- DB models and SQLAlchemy setup: backend/app/db_models.py, backend/app/database.py
- Alembic migrations: backend/alembic/*

### Frontend coupling points
- API client contracts: frontend/src/api.ts
- Module UX flows: frontend/src/App.tsx

## Migration Principles
1. No big-bang rewrite.
2. Keep all intelligence endpoints in FastAPI for now.
3. Move business governance and identity to Django first.
4. Introduce service-to-service auth before major traffic routing.
5. Use measurable phase gates and rollback points.

## What to Move First
### Phase 0: Foundations and Boundary Definition (1-2 weeks)
Move:
- Nothing functionally heavy yet.
- Define clear ownership of endpoints and data models.
Implement:
- Django project scaffold and apps for accounts, orgs, governance.
- Shared API gateway strategy and token propagation model.
Keep in FastAPI:
- All existing routes under /api/v1/*
Estimated effort:
- 6-8 engineer days

### Phase 1: Identity and Governance to Django (2-3 weeks)
Move to Django:
- User registration/login/session/token lifecycle
- Organizations/teams and RBAC
- Governance entities:
  - model approval states
  - promotion approval workflow
  - audit event records
Likely new Django apps:
- control/accounts
- control/organizations
- control/governance
FastAPI changes:
- Accept and validate JWT/service token from Django issuer
- Add governance-aware guards around promote endpoints
Keep in FastAPI:
- Climate train/predict/history/model-list APIs and training runtime
Estimated effort:
- 14-18 engineer days

### Phase 2: Control-plane UI and Reporting in Django (2-3 weeks)
Move to Django:
- Governance dashboards
- Approval queues
- Audit and compliance reports
Frontend impact:
- React app can stay, but route selected pages via Django API or Django-rendered admin for operations users
Keep in FastAPI:
- Intelligence APIs and simulation workflows
Estimated effort:
- 12-16 engineer days

### Phase 3: Workflow Orchestration and Policy Controls (3-4 weeks)
Move to Django:
- Workflow orchestration for model lifecycle approvals
- Policy checks before promotion/deployment actions
- Cross-domain business workflow state machine
FastAPI role:
- Execute compute tasks triggered by Django workflow decisions
Estimated effort:
- 18-24 engineer days

### Phase 4: Optional API Consolidation (only if needed) (3-6 weeks)
Consider moving only low-compute endpoints to Django if operationally beneficial.
Do not move:
- Training/inference/simulation endpoints unless there is a hard non-functional need.
Estimated effort:
- 15-30 engineer days depending on scope

## Module-by-Module Keep/Move Decision with Effort
### Module A: Climate Analytics (existing)
Current files:
- backend/app/services/climate_analytics.py
- backend/app/api/routes.py
- backend/app/models.py
Decision:
- Keep training, predict, history in FastAPI.
- Move promotion approval policy to Django.
Migration work:
- Add pre-promotion approval gate check via Django governance API.
Effort:
- 6-9 engineer days

### Module B: Risk Sandbox (existing)
Current files:
- backend/app/services/risk_engine.py
- backend/app/api/routes.py
Decision:
- Keep scoring and simulation in FastAPI.
- Move user-level access policy and usage limits to Django.
Effort:
- 4-6 engineer days

### Module C: Health Analytics (planned)
Suggested files:
- backend/app/services/health_analytics.py
- backend/app/api/routes.py
Decision:
- Build directly in FastAPI as intelligence module.
- Register module metadata and governance policy in Django.
Effort:
- Build: 10-14 engineer days
- Django governance integration: 3-5 engineer days

### Module D: Cyber Analytics (planned)
Suggested files:
- backend/app/services/cyber_analytics.py
- backend/app/api/routes.py
Decision:
- Build directly in FastAPI.
- Governance and operational controls in Django.
Effort:
- Build: 10-14 engineer days
- Django governance integration: 3-5 engineer days

### Module E: Unified Risk Timeline (planned)
Suggested files:
- backend/app/services/risk_timeline.py
- frontend/src/App.tsx
Decision:
- Hybrid:
  - FastAPI aggregates event signals
  - Django owns policy-scoped visibility and stakeholder reporting views
Effort:
- 8-12 engineer days

### Module F: Knowledge Graph / Digital Twin / Federated (future)
Decision:
- Keep compute engines in FastAPI microservices.
- Use Django as control, approval, and governance shell.
Effort:
- Knowledge graph integration: 15-25 engineer days
- Digital twin orchestration: 20-35 engineer days
- Federated pilot orchestration + policy layer: 25-40 engineer days

## Routing and API Ownership Map
### FastAPI-owned (intelligence)
- /api/v1/climate/train
- /api/v1/climate/predict
- /api/v1/climate/predictions
- /api/v1/risk/predict
- /api/v1/risk/simulate
- Future domain prediction/training routes

### Django-owned (control)
- /control/auth/*
- /control/orgs/*
- /control/roles/*
- /control/governance/*
- /control/reports/*
- /control/workflows/*

### Shared boundary contract
- Request identity context propagated from Django to FastAPI
- Correlation IDs for end-to-end tracing
- Unified error envelope for frontend simplicity

## Concrete Repo Change Plan
### Step 1
Create a new top-level Django service folder:
- control-plane/

### Step 2
Add integration docs and environment wiring:
- update README.md
- add docker-compose service for Django
- add service-to-service environment vars in .env.example

### Step 3
Implement Django control apps and migrations:
- control-plane/apps/accounts
- control-plane/apps/organizations
- control-plane/apps/governance

### Step 4
Add FastAPI auth middleware and governance checks:
- backend/app/api/routes.py
- backend/app/main.py

### Step 5
Update frontend API routing for control endpoints:
- frontend/src/api.ts
- frontend/src/App.tsx

## Risks and Mitigation
### Risk: Team context switching across two frameworks
Mitigation:
- Strict boundary ownership by domain
- Shared API contracts and docs

### Risk: Auth inconsistency between services
Mitigation:
- Single token issuer in Django
- FastAPI trusts issuer and validates signature/claims

### Risk: Delivery slowdown during migration
Mitigation:
- Keep all current FastAPI routes operational
- Move control-plane capabilities incrementally with feature flags

## Recommended 8-Week Execution Timeline
- Week 1-2: Phase 0 (foundation, boundaries, scaffolding)
- Week 3-4: Phase 1 (identity + RBAC + governance core)
- Week 5-6: Phase 2 (control-plane dashboards + reporting)
- Week 7-8: Phase 3 initial slice (approval workflows + policy gates)

## Go/No-Go Checkpoints
- Checkpoint A (end of Week 2): Django scaffold + auth model ready
- Checkpoint B (end of Week 4): RBAC and governance APIs live
- Checkpoint C (end of Week 6): operational dashboard and reporting ready
- Checkpoint D (end of Week 8): model promotion policy enforcement live

## Final Recommendation
For this repo, the best path is hybrid-first:
- Move governance, identity, and business workflows to Django.
- Keep all prediction/training/simulation intelligence in FastAPI.
- Reassess consolidation only after V1 multi-domain modules are stable.
