# PlanetMind 2-Week Sprint Plan

## Sprint Goal
Stabilize the current Climate Analytics MVP for stakeholder demo readiness by hardening core API contracts, migration discipline, model governance UX, and quality gates.

## Sprint Window
- Duration: 2 weeks (10 working days)
- Cadence: Daily standup, mid-sprint review (Day 5), sprint demo + retrospective (Day 10)

## Team and Owners
- Product Manager (PM): Product Owner
- Backend Lead: API + data model delivery
- Frontend Lead: Dashboard and UX flows
- ML Engineer: Climate model lifecycle and evaluation
- DevOps Engineer: Runtime reliability and CI/CD checks
- QA Engineer: Test plan and regression validation

## Capacity and Story Point Target
- Target velocity: 44 story points
- Planned load: 42 story points

## Sprint Backlog
| ID | Story | Owner | Points | Priority |
|---|---|---|---:|---|
| PM-002 | Migration discipline and schema safety | Backend Lead + DevOps Engineer | 8 | P0 |
| PM-003 | API contract stabilization (errors, validation format) | Backend Lead | 5 | P0 |
| PM-010 | Climate model ops metadata and governance trail | ML Engineer + Backend Lead | 8 | P1 |
| PM-011 | Climate UX completion (validation, empty states, table controls) | Frontend Lead | 8 | P1 |
| PM-012 | Regression coverage for API/UI critical paths | QA Engineer + Backend Lead + Frontend Lead | 8 | P1 |
| PM-001 | Startup/runtime consolidation and developer runbook | DevOps Engineer | 5 | P0 |

Total: 42 points

## Day-by-Day Plan
### Week 1
- Day 1
  - Sprint kickoff, scope lock, acceptance criteria validation
  - PM-002 design decisions finalized
- Day 2
  - PM-002 implementation starts
  - PM-003 API error schema draft
- Day 3
  - PM-002 code complete, review opened
  - PM-003 implementation in progress
- Day 4
  - PM-003 completed and integrated
  - PM-001 runtime paths review and script updates
- Day 5 (Mid-sprint Review)
  - PM-001 completion target
  - PM-010 implementation kickoff
  - Risk review and scope adjustment if required

### Week 2
- Day 6
  - PM-010 implementation in progress
  - PM-011 UI hardening starts
- Day 7
  - PM-010 complete with governance metadata endpoints
  - PM-011 table filters, form validation, empty states complete
- Day 8
  - PM-012 test coverage expansion (backend + frontend)
- Day 9
  - Full regression run, bug fixes, demo script preparation
- Day 10
  - Sprint demo, acceptance sign-off, retrospective, next sprint planning

## Definition of Done
- Code merged to main branch with review approval
- Migration included for schema changes
- Automated tests pass in CI
- Updated documentation in README or documents folder
- Feature demonstrable from UI or API endpoint

## Risks and Mitigations
- Risk: Scope creep into V1 items
  - Mitigation: Freeze backlog after Day 2
- Risk: Data/model quality variation
  - Mitigation: Enforce dataset validation checks and metric baselines
- Risk: UI and API contract drift
  - Mitigation: Shared API response schema and contract tests
- Risk: Demo instability
  - Mitigation: Final 2-day stabilization and dry-run

## Sprint Demo Script (Stakeholders)
1. Start platform and verify health
2. Train climate model from dataset
3. Review model versions and promote active version
4. Run climate prediction and inspect history
5. Show improved UX and standardized error handling
