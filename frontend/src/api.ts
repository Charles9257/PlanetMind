export type Domain = "climate" | "health" | "cyber" | "economic";
export type Module = "climate" | "pandemic";

export interface RiskSignal {
  name: string;
  value: number;
}

export interface PredictionResponse {
  domain: Domain;
  region: string;
  score: number;
  severity: string;
  explanation: string;
  top_contributors: Record<string, number>;
}

export interface SimulationResponse {
  baseline_score: number;
  projected_score: number;
  net_reduction: number;
  summary: string;
}

export interface ExplanationPayload {
  base_value: number;
  contributions: Record<string, number>;
}

export interface ModuleTrainResponse {
  module: Module;
  model_run_id: number;
  model_version: number;
  is_active: boolean;
  target_column: string;
  feature_columns: string[];
  rows_trained: number;
  metrics: Record<string, number>;
  governance_synced: boolean;
  governance_status?: string | null;
  governance_error?: string | null;
}

export interface ModuleModelRunItem {
  module: Module;
  model_run_id: number;
  model_version: number;
  is_active: boolean;
  created_at: string;
  promoted_at?: string | null;
  target_column: string;
  feature_columns: string[];
  rows_trained: number;
  metrics: Record<string, number>;
}

export interface ModulePredictResponse {
  module: Module;
  prediction_id: number;
  model_run_id: number;
  model_version: number;
  region?: string | null;
  predicted_risk: number;
  explanation: ExplanationPayload;
  created_at: string;
}

export interface ModulePredictionHistoryItem {
  module: Module;
  prediction_id: number;
  model_run_id: number;
  region?: string | null;
  predicted_risk: number;
  created_at: string;
  feature_payload: Record<string, number>;
  explanation?: ExplanationPayload | null;
}

export interface AgentStepItem {
  name: string;
  status: string;
  duration_ms: number;
  output: Record<string, unknown>;
}

export interface AgentPipelineRunResponse {
  agent_run_id: number;
  module: Module;
  region?: string | null;
  status: string;
  steps: AgentStepItem[];
  final_output: Record<string, unknown>;
  created_at: string;
}

export interface FederatedTrainResponse {
  federated_run_id: number;
  module: Module;
  num_clients: number;
  rounds: number;
  target_column: string;
  feature_columns: string[];
  client_sample_counts: number[];
  federated_metrics: Record<string, number>;
  centralized_metrics: Record<string, number>;
  created_at: string;
}

export interface KnowledgeGraphNode {
  id: string;
  label: string;
  type: string;
}

export interface KnowledgeGraphEdge {
  source: string;
  target: string;
  relation: string;
}

export interface KnowledgeGraphResponse {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
}

export interface GovernanceLoginResponse {
  access: string;
  refresh?: string;
}

export interface GovernanceApprovalItem {
  id: number;
  model_entry: number;
  model_entry_data: {
    id: number;
    organization: number;
    source_system: string;
    external_model_run_id: number;
    module: string;
    model_name: string;
    model_version: string;
    is_active: boolean;
    created_at: string;
  };
  requested_by: number;
  decided_by?: number | null;
  status: string;
  decision_notes: string;
  requested_at: string;
  decided_at?: string | null;
}

export interface GovernanceStatusResponse {
  approved: boolean;
  status: string;
  source_system: string;
  external_model_run_id: number;
  approval_id?: number | null;
  model_entry_id?: number | null;
  organization_id?: number | null;
}

export interface OrganizationItem {
  id: number;
  name: string;
  slug: string;
  created_at: string;
  member_count?: number;
}

export interface GovernanceUserItem {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
}

export type MembershipRole = "admin" | "member" | "analyst" | "viewer";

export interface MembershipItem {
  id: number;
  user?: number;
  user_id: number;
  username: string;
  email: string;
  organization: number;
  organization_name: string;
  role: MembershipRole;
  created_at: string;
}

export interface PaginatedResponse<T> {
  count: number;
  page: number;
  page_size: number;
  results: T[];
}

export interface AuditEventItem {
  id: number;
  actor?: number | null;
  actor_username?: string | null;
  event_type: string;
  entity_type: string;
  entity_id: string;
  payload: Record<string, unknown>;
  created_at: string;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const CONTROL_BASE = import.meta.env.VITE_CONTROL_PLANE_BASE_URL ?? "http://localhost:8100";

export async function predictRisk(domain: Domain, region: string, signals: RiskSignal[]): Promise<PredictionResponse> {
  const response = await fetch(`${API_BASE}/api/v1/risk/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ domain, region, signals })
  });
  if (!response.ok) {
    throw new Error(`Prediction failed: ${response.status}`);
  }
  return response.json();
}

export async function simulateRisk(
  baselineScore: number,
  interventions: Array<{ name: string; expected_reduction: number }>
): Promise<SimulationResponse> {
  const response = await fetch(`${API_BASE}/api/v1/risk/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ baseline_score: baselineScore, interventions })
  });
  if (!response.ok) {
    throw new Error(`Simulation failed: ${response.status}`);
  }
  return response.json();
}

export async function trainModuleModel(
  module: Module,
  dataset: File,
  targetColumn = "risk_score"
): Promise<ModuleTrainResponse> {
  const formData = new FormData();
  formData.append("dataset", dataset);
  formData.append("target_column", targetColumn);

  const response = await fetch(`${API_BASE}/api/v1/${module}/train`, {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(`${module} train failed: ${response.status} ${message}`);
  }
  return response.json();
}

export async function listModuleModels(module: Module, limit = 50): Promise<ModuleModelRunItem[]> {
  const response = await fetch(`${API_BASE}/api/v1/${module}/models?limit=${limit}`);
  if (!response.ok) {
    throw new Error(`${module} models fetch failed: ${response.status}`);
  }
  return response.json();
}

export async function promoteModuleModel(module: Module, modelRunId: number): Promise<ModuleModelRunItem> {
  const response = await fetch(`${API_BASE}/api/v1/${module}/models/${modelRunId}/promote`, {
    method: "POST"
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(`${module} model promotion failed: ${response.status} ${message}`);
  }
  return response.json();
}

export async function predictModuleRisk(
  module: Module,
  payload: { region?: string; model_run_id?: number; features: Record<string, number> }
): Promise<ModulePredictResponse> {
  const response = await fetch(`${API_BASE}/api/v1/${module}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(`${module} prediction failed: ${response.status} ${message}`);
  }
  return response.json();
}

export async function listModulePredictions(module: Module, limit = 20): Promise<ModulePredictionHistoryItem[]> {
  const response = await fetch(`${API_BASE}/api/v1/${module}/predictions?limit=${limit}`);
  if (!response.ok) {
    throw new Error(`${module} prediction history fetch failed: ${response.status}`);
  }
  return response.json();
}

export async function runAgentPipeline(payload: {
  module: Module;
  region?: string;
  features: Record<string, number>;
  model_run_id?: number;
  interventions?: Array<{ name: string; expected_reduction: number }>;
}): Promise<AgentPipelineRunResponse> {
  const response = await fetch(`${API_BASE}/api/v1/agents/pipeline/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(`Agent pipeline run failed: ${response.status} ${message}`);
  }
  return response.json();
}

export async function listAgentPipelineRuns(limit = 20): Promise<AgentPipelineRunResponse[]> {
  const response = await fetch(`${API_BASE}/api/v1/agents/pipeline/runs?limit=${limit}`);
  if (!response.ok) {
    throw new Error(`Agent pipeline history fetch failed: ${response.status}`);
  }
  return response.json();
}

export async function trainFederatedModel(
  module: Module,
  dataset: File,
  targetColumn = "risk_score",
  numClients = 3,
  rounds = 10
): Promise<FederatedTrainResponse> {
  const formData = new FormData();
  formData.append("dataset", dataset);
  formData.append("target_column", targetColumn);
  formData.append("num_clients", String(numClients));
  formData.append("rounds", String(rounds));

  const response = await fetch(`${API_BASE}/api/v1/${module}/federated/train`, {
    method: "POST",
    body: formData
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(`${module} federated training failed: ${response.status} ${message}`);
  }
  return response.json();
}

export async function listFederatedRuns(module: Module, limit = 20): Promise<FederatedTrainResponse[]> {
  const response = await fetch(`${API_BASE}/api/v1/${module}/federated/runs?limit=${limit}`);
  if (!response.ok) {
    throw new Error(`${module} federated run history fetch failed: ${response.status}`);
  }
  return response.json();
}

export async function getKnowledgeGraph(limitPredictions = 100): Promise<KnowledgeGraphResponse> {
  const response = await fetch(`${API_BASE}/api/v1/knowledge-graph?limit_predictions=${limitPredictions}`);
  if (!response.ok) {
    throw new Error(`Knowledge graph fetch failed: ${response.status}`);
  }
  return response.json();
}

export async function loginGovernance(username: string, password: string): Promise<GovernanceLoginResponse> {
  const response = await fetch(`${CONTROL_BASE}/control/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(`Governance login failed: ${response.status} ${message}`);
  }
  return response.json();
}

export async function listGovernanceApprovals(token: string): Promise<GovernanceApprovalItem[]> {
  const response = await fetch(`${CONTROL_BASE}/control/governance/approvals/`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(`Governance approvals fetch failed: ${response.status} ${message}`);
  }
  return response.json();
}

export async function getGovernanceStatus(token: string, modelRunId: number): Promise<GovernanceStatusResponse> {
  const response = await fetch(
    `${CONTROL_BASE}/control/governance/approvals/status/?external_model_run_id=${modelRunId}&source_system=fastapi`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  if (!response.ok) {
    const message = await response.text();
    throw new Error(`Governance status fetch failed: ${response.status} ${message}`);
  }
  return response.json();
}

export async function decideGovernanceApproval(
  token: string,
  approvalId: number,
  status: "approved" | "rejected",
  decisionNotes: string
): Promise<GovernanceApprovalItem> {
  const response = await fetch(`${CONTROL_BASE}/control/governance/approvals/${approvalId}/decide/`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ status, decision_notes: decisionNotes })
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(`Governance decision failed: ${response.status} ${message}`);
  }
  return response.json();
}

export async function listOrganizations(token: string): Promise<OrganizationItem[]> {
  const response = await fetch(`${CONTROL_BASE}/control/orgs/`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(`Organizations fetch failed: ${response.status} ${message}`);
  }
  return response.json();
}

export async function listOrganizationUsers(token: string, search = ""): Promise<GovernanceUserItem[]> {
  const suffix = search ? `?search=${encodeURIComponent(search)}` : "";
  const response = await fetch(`${CONTROL_BASE}/control/orgs/users/${suffix}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(`Governance users fetch failed: ${response.status} ${message}`);
  }
  return response.json();
}

export async function listMemberships(
  token: string,
  organizationId?: number,
  page = 1,
  pageSize = 10,
  filters?: { role?: string; username?: string }
): Promise<PaginatedResponse<MembershipItem>> {
  const params = new URLSearchParams();
  if (organizationId) params.set("organization", String(organizationId));
  params.set("page", String(page));
  params.set("page_size", String(pageSize));
  if (filters?.role) params.set("role", filters.role);
  if (filters?.username) params.set("username", filters.username);
  const suffix = `?${params.toString()}`;
  const response = await fetch(`${CONTROL_BASE}/control/orgs/memberships/${suffix}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(`Memberships fetch failed: ${response.status} ${message}`);
  }
  return response.json();
}

export async function createMembership(
  token: string,
  organizationId: number,
  username: string,
  role: MembershipRole
): Promise<MembershipItem> {
  const response = await fetch(`${CONTROL_BASE}/control/orgs/memberships/`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ organization: organizationId, input_username: username, role })
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(`Create membership failed: ${response.status} ${message}`);
  }
  return response.json();
}

export async function updateMembershipRole(
  token: string,
  membershipId: number,
  organizationId: number,
  role: MembershipRole
): Promise<MembershipItem> {
  const response = await fetch(`${CONTROL_BASE}/control/orgs/memberships/${membershipId}/`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ organization: organizationId, role })
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(`Update membership failed: ${response.status} ${message}`);
  }
  return response.json();
}

export async function deleteMembership(token: string, membershipId: number): Promise<void> {
  const response = await fetch(`${CONTROL_BASE}/control/orgs/memberships/${membershipId}/`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(`Delete membership failed: ${response.status} ${message}`);
  }
}

export async function listAuditEvents(
  token: string,
  filters: {
    eventType?: string;
    entityType?: string;
    organizationId?: number;
    externalModelRunId?: string;
    actorUsername?: string;
    page?: number;
    pageSize?: number;
  }
): Promise<PaginatedResponse<AuditEventItem>> {
  const params = new URLSearchParams();
  if (filters.eventType) params.set("event_type", filters.eventType);
  if (filters.entityType) params.set("entity_type", filters.entityType);
  if (filters.organizationId) params.set("organization_id", String(filters.organizationId));
  if (filters.externalModelRunId) params.set("external_model_run_id", filters.externalModelRunId);
  if (filters.actorUsername) params.set("actor_username", filters.actorUsername);
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.pageSize ?? 10));
  const suffix = params.toString() ? `?${params.toString()}` : "";

  const response = await fetch(`${CONTROL_BASE}/control/governance/audit/${suffix}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(`Audit events fetch failed: ${response.status} ${message}`);
  }
  return response.json();
}
