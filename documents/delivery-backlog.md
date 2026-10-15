# PlanetMind Delivery Backlog (Mapped to Current Codebase)

## How to Use This Backlog
- Priority order: P0 -> P1 -> P2
- Each item maps directly to existing files for straightforward execution
- Acceptance criteria are testable in API/UI workflows

## P0 (Foundation Hardening)

### PM-001 Environment and Runtime Consolidation
- Objective: make startup paths consistent for local and container runs
- Existing files:
  - backend/app/main.py
  - backend/Dockerfile
  - docker-compose.yml
  - start-dev-windows.bat
- Tasks:
  - unify env var handling and defaults
  - add explicit backend readiness check in compose
  - document one canonical dev startup path
- Acceptance criteria:
  - one-command startup works reliably
  - health endpoint responds after startup in all supported modes

### PM-002 Migration Discipline and Schema Safety
- Objective: enforce migration-first DB evolution
- Existing files:
  - backend/alembic.ini
  - backend/alembic/env.py
  - backend/alembic/versions/20260710_0001_create_climate_tables.py
  - backend/app/db_models.py
- Tasks:
  - add migration runbook and naming standard
  - add CI check for pending model-vs-schema drift
- Acceptance criteria:
  - schema changes always represented in Alembic revisions
  - migrations apply cleanly on empty DB and existing DB

### PM-003 API Contract Stabilization
- Objective: standardize API response envelope and error format
- Existing files:
  - backend/app/api/routes.py
  - backend/app/models.py
- Tasks:
  - define common error schema
  - add consistent validation error handling
- Acceptance criteria:
  - all endpoints return standardized error payloads
  - frontend can render errors uniformly

## P1 (MVP Completion)

### PM-010 Climate Model Ops Enhancements
- Objective: improve governance and model lifecycle visibility
- Existing files:
  - backend/app/services/climate_analytics.py
  - backend/app/api/routes.py
  - backend/app/models.py
- Tasks:
  - add model metadata: data version, training params, model notes
  - expose active model history and promotion audit trail
- Acceptance criteria:
  - model list includes full governance metadata
  - promotion trail is queryable and visible in UI

### PM-011 Frontend Climate UX Completion
- Objective: polish and harden climate workflows for analyst usage
- Existing files:
  - frontend/src/App.tsx
  - frontend/src/api.ts
  - frontend/src/styles.css
- Tasks:
  - add form validation and empty-state UX
  - add optimistic loading and retry guidance
  - add filtering/sorting on history and model tables
- Acceptance criteria:
  - no blocking UX dead-ends
  - analysts can complete train->predict->review loop without CLI

### PM-012 Quality and Regression Coverage
- Objective: protect critical workflows with automated tests
- Existing files:
  - backend/tests/test_api.py
  - frontend/package.json
- Tasks:
  - expand backend tests for error paths and edge cases
  - add frontend component/integration tests for key screens
- Acceptance criteria:
  - core APIs and UI flows covered with passing tests
  - regressions are caught before merge

## P2 (V1 Multi-Domain Expansion)

### PM-020 Health Analytics Module (Module 2)
- Objective: add health risk prediction module with same lifecycle controls
- Existing files to extend:
  - backend/app/models.py
  - backend/app/api/routes.py
  - backend/app/services/
  - frontend/src/api.ts
  - frontend/src/App.tsx
- New files suggested:
  - backend/app/services/health_analytics.py
  - backend/alembic/versions/<revision>_add_health_tables.py
- Acceptance criteria:
  - train/predict/history endpoints for health module
  - UI module card and workflow parity with climate

### PM-021 Cyber Analytics Module (Module 3)
- Objective: add cyber threat prediction baseline
- Existing files to extend:
  - backend/app/models.py
  - backend/app/api/routes.py
  - frontend/src/api.ts
  - frontend/src/App.tsx
- New files suggested:
  - backend/app/services/cyber_analytics.py
  - backend/alembic/versions/<revision>_add_cyber_tables.py
- Acceptance criteria:
  - cyber module follows same governance and API patterns
  - unified module navigation and reporting in UI

### PM-022 Unified Risk Timeline
- Objective: aggregate cross-module predictions into one timeline
- Existing files:
  - backend/app/db_models.py
  - backend/app/api/routes.py
  - frontend/src/App.tsx
- New files suggested:
  - backend/app/services/risk_timeline.py
- Acceptance criteria:
  - dashboard shows unified chronological risk events across modules

## P3 (V2+ Strategic Items)

### PM-030 Knowledge Graph Foundation
- Objective: represent entity/event relationships for cross-domain reasoning
- Existing integration points:
  - backend/app/services/
  - backend/app/api/routes.py
- New components suggested:
  - backend/app/services/knowledge_graph.py
  - graph connector configuration
- Acceptance criteria:
  - graph queries available for at least one cross-domain scenario

### PM-031 Digital Twin Scenario Engine
- Objective: simulate interventions and compare outcomes
- Existing integration points:
  - backend/app/services/risk_engine.py
  - frontend/src/App.tsx
- New components suggested:
  - backend/app/services/digital_twin.py
  - scenario API contracts in backend/app/models.py
- Acceptance criteria:
  - users can run scenario A/B and compare projected outcomes

### PM-032 Federated Learning Pilot
- Objective: evaluate privacy-preserving multi-node training setup
- Existing integration points:
  - backend/app/services/climate_analytics.py
- New components suggested:
  - backend/app/services/federated/
  - backend/app/services/federated_orchestrator.py
- Acceptance criteria:
  - pilot training runs across simulated nodes with measurable quality/privacy tradeoff

## Sprint-Ready Starter Sequence (Recommended)
1. PM-002 Migration discipline
2. PM-003 API contract stabilization
3. PM-010 Climate model ops enhancements
4. PM-011 Frontend climate UX completion
5. PM-012 Quality/regression coverage

## Definition of Done (for all backlog items)
- Code implemented in mapped files
- Relevant migrations included when schema changes
- Tests added/updated and passing
- README/documentation updated
- Demonstrable via API or UI workflow
