import { FormEvent, useEffect, useState } from "react";
import {
  AuditEventItem,
  GovernanceApprovalItem,
  GovernanceStatusResponse,
  GovernanceUserItem,
  MembershipItem,
  MembershipRole,
  OrganizationItem,
  createMembership,
  deleteMembership,
  decideGovernanceApproval,
  getGovernanceStatus,
  listAuditEvents,
  listGovernanceApprovals,
  listMemberships,
  listModuleModels,
  listOrganizationUsers,
  listOrganizations,
  loginGovernance,
  updateMembershipRole
} from "../api";
import { useRevealSections } from "../hooks/useRevealSections";

const GOVERNANCE_TOKEN_KEY = "planetmind.governanceToken";
const GOVERNANCE_USERNAME_KEY = "planetmind.governanceUsername";
const MEMBERSHIP_PAGE_SIZE = 5;
const AUDIT_PAGE_SIZE = 5;

export function Governance() {
  useRevealSections();

  const [governanceToken, setGovernanceToken] = useState<string>("");
  const [governanceUsername, setGovernanceUsername] = useState("orgadmin");
  const [governancePassword, setGovernancePassword] = useState("pass12345");
  const [governanceApprovals, setGovernanceApprovals] = useState<GovernanceApprovalItem[]>([]);
  const [governanceStatus, setGovernanceStatus] = useState<GovernanceStatusResponse | null>(null);
  const [governanceLookupRunId, setGovernanceLookupRunId] = useState<string>("");
  const [governanceDecisionNote, setGovernanceDecisionNote] = useState("Ready for promotion review.");
  const [loadingGovernance, setLoadingGovernance] = useState(false);
  const [loadingMemberships, setLoadingMemberships] = useState(false);
  const [loadingAudit, setLoadingAudit] = useState(false);
  const [errorGovernance, setErrorGovernance] = useState<string | null>(null);
  const [organizations, setOrganizations] = useState<OrganizationItem[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<number | null>(null);
  const [memberships, setMemberships] = useState<MembershipItem[]>([]);
  const [governanceUsers, setGovernanceUsers] = useState<GovernanceUserItem[]>([]);
  const [membershipUsername, setMembershipUsername] = useState("");
  const [membershipRole, setMembershipRole] = useState<MembershipRole>("member");
  const [auditEvents, setAuditEvents] = useState<AuditEventItem[]>([]);
  const [auditEventType, setAuditEventType] = useState("");
  const [auditEntityType, setAuditEntityType] = useState("");
  const [auditActorUsername, setAuditActorUsername] = useState("");
  const [auditExternalModelRunId, setAuditExternalModelRunId] = useState("");
  const [membershipPage, setMembershipPage] = useState(1);
  const [auditPage, setAuditPage] = useState(1);
  const [membershipTotal, setMembershipTotal] = useState(0);
  const [auditTotal, setAuditTotal] = useState(0);
  const [membershipUsernameFilter, setMembershipUsernameFilter] = useState("");
  const [membershipRoleFilter, setMembershipRoleFilter] = useState("");

  const membershipPageCount = Math.max(1, Math.ceil(membershipTotal / MEMBERSHIP_PAGE_SIZE));
  const auditPageCount = Math.max(1, Math.ceil(auditTotal / AUDIT_PAGE_SIZE));

  const loadMembershipPage = async (token: string, organizationId: number, page = membershipPage) => {
    setLoadingMemberships(true);
    const payload = await listMemberships(token, organizationId, page, MEMBERSHIP_PAGE_SIZE, {
      role: membershipRoleFilter || undefined,
      username: membershipUsernameFilter || undefined
    });
    setMemberships(payload.results);
    setMembershipTotal(payload.count);
    setMembershipPage(payload.page);
    setLoadingMemberships(false);
  };

  const loadAuditPage = async (token: string, organizationId: number, page = auditPage) => {
    setLoadingAudit(true);
    const payload = await listAuditEvents(token, {
      eventType: auditEventType || undefined,
      entityType: auditEntityType || undefined,
      organizationId,
      externalModelRunId: auditExternalModelRunId || undefined,
      actorUsername: auditActorUsername || undefined,
      page,
      pageSize: AUDIT_PAGE_SIZE
    });
    setAuditEvents(payload.results);
    setAuditTotal(payload.count);
    setAuditPage(payload.page);
    setLoadingAudit(false);
  };

  const refreshGovernanceData = async (token: string, modelRunId?: number) => {
    const [approvals, orgs] = await Promise.all([listGovernanceApprovals(token), listOrganizations(token)]);
    setGovernanceApprovals(approvals);
    setOrganizations(orgs);

    const effectiveOrgId = selectedOrgId ?? orgs[0]?.id ?? null;
    if (effectiveOrgId) {
      setSelectedOrgId(effectiveOrgId);
      const users = await listOrganizationUsers(token);
      setGovernanceUsers(users);
      await Promise.all([loadMembershipPage(token, effectiveOrgId, 1), loadAuditPage(token, effectiveOrgId, 1)]);
    }

    let lookupId = modelRunId;
    if (!lookupId) {
      const climateModels = await listModuleModels("climate", 50).catch(() => []);
      lookupId = climateModels.find((m) => m.is_active)?.model_run_id;
    }
    if (lookupId) {
      const statusResult = await getGovernanceStatus(token, lookupId);
      setGovernanceStatus(statusResult);
      setGovernanceLookupRunId(String(lookupId));
    }
  };

  useEffect(() => {
    const savedToken = window.localStorage.getItem(GOVERNANCE_TOKEN_KEY);
    const savedUsername = window.localStorage.getItem(GOVERNANCE_USERNAME_KEY);
    if (savedToken) {
      setGovernanceToken(savedToken);
    }
    if (savedUsername) {
      setGovernanceUsername(savedUsername);
    }
  }, []);

  useEffect(() => {
    if (!governanceToken) {
      return;
    }
    refreshGovernanceData(governanceToken).catch((err) => {
      setErrorGovernance(err instanceof Error ? err.message : "Failed to load governance data");
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [governanceToken]);

  const onGovernanceLogin = async (event: FormEvent) => {
    event.preventDefault();
    setLoadingGovernance(true);
    setErrorGovernance(null);
    try {
      const result = await loginGovernance(governanceUsername, governancePassword);
      setGovernanceToken(result.access);
      window.localStorage.setItem(GOVERNANCE_TOKEN_KEY, result.access);
      window.localStorage.setItem(GOVERNANCE_USERNAME_KEY, governanceUsername);
      await refreshGovernanceData(result.access);
    } catch (err) {
      setErrorGovernance(err instanceof Error ? err.message : "Governance login failed");
    } finally {
      setLoadingGovernance(false);
    }
  };

  const clearGovernanceSession = (message?: string) => {
    setGovernanceToken("");
    setGovernanceApprovals([]);
    setGovernanceStatus(null);
    setOrganizations([]);
    setMemberships([]);
    setAuditEvents([]);
    window.localStorage.removeItem(GOVERNANCE_TOKEN_KEY);
    if (message) {
      setErrorGovernance(message);
    }
  };

  const normalizeGovernanceError = (err: unknown, fallback: string) => {
    const message = err instanceof Error ? err.message : fallback;
    if (/401|403|session expired|invalid token|token/i.test(message)) {
      clearGovernanceSession("Governance session expired. Please sign in again.");
    }
    return message;
  };

  const onGovernanceLookup = async (event: FormEvent) => {
    event.preventDefault();
    if (!governanceToken || !governanceLookupRunId) {
      return;
    }
    setLoadingGovernance(true);
    setErrorGovernance(null);
    try {
      const result = await getGovernanceStatus(governanceToken, Number(governanceLookupRunId));
      setGovernanceStatus(result);
    } catch (err) {
      setErrorGovernance(normalizeGovernanceError(err, "Governance status lookup failed"));
    } finally {
      setLoadingGovernance(false);
    }
  };

  const onGovernanceDecision = async (approvalId: number, status: "approved" | "rejected") => {
    if (!governanceToken) {
      return;
    }
    setLoadingGovernance(true);
    setErrorGovernance(null);
    try {
      await decideGovernanceApproval(governanceToken, approvalId, status, governanceDecisionNote);
      await refreshGovernanceData(governanceToken, Number(governanceLookupRunId || 0) || undefined);
    } catch (err) {
      setErrorGovernance(normalizeGovernanceError(err, "Governance decision failed"));
    } finally {
      setLoadingGovernance(false);
    }
  };

  const onMembershipCreate = async (event: FormEvent) => {
    event.preventDefault();
    if (!governanceToken || !selectedOrgId || !membershipUsername) {
      return;
    }
    setLoadingGovernance(true);
    setLoadingMemberships(true);
    setErrorGovernance(null);
    try {
      await createMembership(governanceToken, selectedOrgId, membershipUsername, membershipRole);
      setMembershipUsername("");
      await loadMembershipPage(governanceToken, selectedOrgId, 1);
    } catch (err) {
      setErrorGovernance(normalizeGovernanceError(err, "Create membership failed"));
    } finally {
      setLoadingMemberships(false);
      setLoadingGovernance(false);
    }
  };

  const onMembershipRoleChange = async (membershipId: number, role: MembershipRole) => {
    if (!governanceToken || !selectedOrgId) {
      return;
    }
    setLoadingGovernance(true);
    setLoadingMemberships(true);
    setErrorGovernance(null);
    try {
      await updateMembershipRole(governanceToken, membershipId, selectedOrgId, role);
      await loadMembershipPage(governanceToken, selectedOrgId, membershipPage);
    } catch (err) {
      setErrorGovernance(normalizeGovernanceError(err, "Update membership failed"));
    } finally {
      setLoadingMemberships(false);
      setLoadingGovernance(false);
    }
  };

  const onMembershipDelete = async (membershipId: number) => {
    if (!governanceToken || !selectedOrgId) {
      return;
    }
    setLoadingGovernance(true);
    setLoadingMemberships(true);
    setErrorGovernance(null);
    try {
      await deleteMembership(governanceToken, membershipId);
      const nextPage = membershipPage > 1 && memberships.length === 1 ? membershipPage - 1 : membershipPage;
      await loadMembershipPage(governanceToken, selectedOrgId, nextPage);
    } catch (err) {
      setErrorGovernance(normalizeGovernanceError(err, "Delete membership failed"));
    } finally {
      setLoadingMemberships(false);
      setLoadingGovernance(false);
    }
  };

  const onAuditFilter = async (event: FormEvent) => {
    event.preventDefault();
    if (!governanceToken) {
      return;
    }
    setLoadingGovernance(true);
    setLoadingAudit(true);
    setErrorGovernance(null);
    try {
      if (selectedOrgId) {
        await loadAuditPage(governanceToken, selectedOrgId, 1);
      }
    } catch (err) {
      setErrorGovernance(normalizeGovernanceError(err, "Audit filter failed"));
    } finally {
      setLoadingAudit(false);
      setLoadingGovernance(false);
    }
  };

  return (
    <>
      <section className="card reveal-section governance-hero">
        <h2>Governance Control Plane</h2>
        <p>
          Review approval queues, inspect model-run approval status, and transition pending promotion requests with
          auditable decisions.
        </p>
      </section>

      {!governanceToken ? (
        <section className="card reveal-section">
          <h2>1) Governance Login</h2>
          <form className="grid-2" onSubmit={onGovernanceLogin}>
            <label>
              Username
              <input value={governanceUsername} onChange={(e) => setGovernanceUsername(e.target.value)} />
            </label>
            <label>
              Password
              <input type="password" value={governancePassword} onChange={(e) => setGovernancePassword(e.target.value)} />
            </label>
            <button type="submit" className="span-2" disabled={loadingGovernance}>
              {loadingGovernance ? "Signing in..." : "Sign In to Governance"}
            </button>
          </form>
        </section>
      ) : (
        <>
          <section className="card reveal-section session-banner">
            <div>
              <h2>Active Governance Session</h2>
              <p className="hint">Signed in as {governanceUsername}. Session is stored locally for this browser.</p>
            </div>
            <button type="button" className="secondary" onClick={() => clearGovernanceSession()}>
              Logout
            </button>
          </section>

          <section className="card reveal-section governance-grid">
            <article className="governance-panel">
              <h2>2) Approval Status Lookup</h2>
              <form className="grid-2" onSubmit={onGovernanceLookup}>
                <label>
                  FastAPI Model Run ID
                  <input value={governanceLookupRunId} onChange={(e) => setGovernanceLookupRunId(e.target.value)} />
                </label>
                <div className="governance-actions-row">
                  <button type="submit" disabled={loadingGovernance || !governanceLookupRunId}>
                    {loadingGovernance ? "Checking..." : "Check Status"}
                  </button>
                </div>
              </form>
              {governanceStatus ? (
                <div className="status-card">
                  <p className={`status-pill ${governanceStatus.approved ? "status-approved" : governanceStatus.status === "pending" ? "status-pending" : "status-rejected"}`}>
                    {governanceStatus.status}
                  </p>
                  <p className="hint">Model Run #{governanceStatus.external_model_run_id}</p>
                </div>
              ) : null}
            </article>

            <article className="governance-panel">
              <h2>3) Decision Notes</h2>
              <label>
                Shared review note
                <input value={governanceDecisionNote} onChange={(e) => setGovernanceDecisionNote(e.target.value)} />
              </label>
              <p className="hint">This note is attached to approve/reject actions from the queue below.</p>
            </article>
          </section>

          <section className="card reveal-section">
            <h2>4) Approval Queue</h2>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Approval</th>
                    <th>Model Run</th>
                    <th>Module</th>
                    <th>Version</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {governanceApprovals.map((approval) => (
                    <tr key={approval.id}>
                      <td>{approval.id}</td>
                      <td>{approval.model_entry_data.external_model_run_id}</td>
                      <td>{approval.model_entry_data.module}</td>
                      <td>{approval.model_entry_data.model_version}</td>
                      <td>
                        <span className={`status-pill ${approval.status === "approved" ? "status-approved" : approval.status === "pending" ? "status-pending" : "status-rejected"}`}>
                          {approval.status}
                        </span>
                      </td>
                      <td>
                        <div className="approval-actions">
                          <button
                            type="button"
                            disabled={loadingGovernance || approval.status !== "pending"}
                            onClick={() => onGovernanceDecision(approval.id, "approved")}
                          >
                            Approve
                          </button>
                          <button
                            type="button"
                            className="secondary"
                            disabled={loadingGovernance || approval.status !== "pending"}
                            onClick={() => onGovernanceDecision(approval.id, "rejected")}
                          >
                            Reject
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="card reveal-section governance-grid governance-grid-wide">
            <article className="governance-panel">
              <h2>5) Organization Memberships</h2>
              <label>
                Active organization
                <select
                  value={selectedOrgId ?? ""}
                  onChange={async (e) => {
                    const nextId = Number(e.target.value);
                    setSelectedOrgId(nextId);
                    if (governanceToken) {
                      await Promise.all([loadMembershipPage(governanceToken, nextId, 1), loadAuditPage(governanceToken, nextId, 1)]);
                    }
                  }}
                >
                  {organizations.map((org) => (
                    <option key={org.id} value={org.id}>
                      {org.name}
                    </option>
                  ))}
                </select>
              </label>

              <form className="grid-2" onSubmit={onMembershipCreate}>
                <label>
                  Username filter
                  <input value={membershipUsernameFilter} onChange={(e) => setMembershipUsernameFilter(e.target.value)} />
                </label>
                <label>
                  Role filter
                  <select value={membershipRoleFilter} onChange={(e) => setMembershipRoleFilter(e.target.value)}>
                    <option value="">All roles</option>
                    <option value="viewer">Viewer</option>
                    <option value="member">Member</option>
                    <option value="analyst">Analyst</option>
                    <option value="admin">Admin</option>
                  </select>
                </label>
                <label>
                  Existing username
                  <input
                    list="governance-users"
                    value={membershipUsername}
                    onChange={(e) => setMembershipUsername(e.target.value)}
                  />
                  <datalist id="governance-users">
                    {governanceUsers.map((user) => (
                      <option key={user.id} value={user.username}>
                        {user.email}
                      </option>
                    ))}
                  </datalist>
                </label>
                <label>
                  Role
                  <select value={membershipRole} onChange={(e) => setMembershipRole(e.target.value as MembershipRole)}>
                    <option value="viewer">Viewer</option>
                    <option value="member">Member</option>
                    <option value="analyst">Analyst</option>
                    <option value="admin">Admin</option>
                  </select>
                </label>
                <button type="submit" className="span-2" disabled={loadingGovernance || !selectedOrgId}>
                  Add Membership
                </button>
              </form>

              <div className="table-wrap">
                {loadingMemberships ? <p className="empty-state">Loading memberships...</p> : null}
                {!loadingMemberships && memberships.length === 0 ? (
                  <p className="empty-state">No memberships found for this organization yet.</p>
                ) : null}
                {!loadingMemberships && memberships.length > 0 ? (
                  <>
                    <table>
                      <thead>
                        <tr>
                          <th>User</th>
                          <th>Email</th>
                          <th>Role</th>
                          <th>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {memberships.map((membership) => (
                          <tr key={membership.id}>
                            <td>{membership.username}</td>
                            <td>{membership.email || "-"}</td>
                            <td>
                              <select
                                value={membership.role}
                                onChange={(e) => onMembershipRoleChange(membership.id, e.target.value as MembershipRole)}
                              >
                                <option value="viewer">Viewer</option>
                                <option value="member">Member</option>
                                <option value="analyst">Analyst</option>
                                <option value="admin">Admin</option>
                              </select>
                            </td>
                            <td>
                              <button
                                type="button"
                                className="secondary"
                                disabled={loadingGovernance}
                                onClick={() => onMembershipDelete(membership.id)}
                              >
                                Remove
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    <div className="pager-row">
                      <button
                        type="button"
                        className="secondary"
                        disabled={membershipPage <= 1 || !selectedOrgId || loadingMemberships}
                        onClick={() => selectedOrgId && governanceToken && loadMembershipPage(governanceToken, selectedOrgId, membershipPage - 1)}
                      >
                        Previous
                      </button>
                      <span className="hint">Page {membershipPage} of {membershipPageCount}</span>
                      <button
                        type="button"
                        className="secondary"
                        disabled={membershipPage >= membershipPageCount || !selectedOrgId || loadingMemberships}
                        onClick={() => selectedOrgId && governanceToken && loadMembershipPage(governanceToken, selectedOrgId, membershipPage + 1)}
                      >
                        Next
                      </button>
                    </div>
                  </>
                ) : null}
              </div>
            </article>

            <article className="governance-panel">
              <h2>6) Audit Timeline</h2>
              <form className="grid-2" onSubmit={onAuditFilter}>
                <label>
                  Event Type
                  <input value={auditEventType} onChange={(e) => setAuditEventType(e.target.value)} />
                </label>
                <label>
                  Entity Type
                  <input value={auditEntityType} onChange={(e) => setAuditEntityType(e.target.value)} />
                </label>
                <label>
                  Actor Username
                  <input value={auditActorUsername} onChange={(e) => setAuditActorUsername(e.target.value)} />
                </label>
                <label>
                  External Model Run ID
                  <input value={auditExternalModelRunId} onChange={(e) => setAuditExternalModelRunId(e.target.value)} />
                </label>
                <button type="submit" className="span-2" disabled={loadingGovernance}>
                  Apply Audit Filters
                </button>
              </form>

              <div className="audit-timeline">
                {loadingAudit ? <p className="empty-state">Loading audit events...</p> : null}
                {!loadingAudit && auditEvents.length === 0 ? <p className="empty-state">No audit events match the current filters.</p> : null}
                {!loadingAudit && auditEvents.map((event) => (
                  <article key={event.id} className="audit-item">
                    <div className="audit-meta">
                      <span className="status-pill status-pending">{event.event_type}</span>
                      <span>{new Date(event.created_at).toLocaleString()}</span>
                    </div>
                    <p className="hint">
                      Actor: {event.actor_username ?? "system"} | Entity: {event.entity_type} #{event.entity_id}
                    </p>
                    <pre className="audit-payload">{JSON.stringify(event.payload, null, 2)}</pre>
                  </article>
                ))}
                {!loadingAudit && auditEvents.length > 0 ? (
                  <div className="pager-row">
                    <button
                      type="button"
                      className="secondary"
                      disabled={auditPage <= 1 || !selectedOrgId || loadingAudit}
                      onClick={() => selectedOrgId && governanceToken && loadAuditPage(governanceToken, selectedOrgId, auditPage - 1)}
                    >
                      Previous
                    </button>
                    <span className="hint">Page {auditPage} of {auditPageCount}</span>
                    <button
                      type="button"
                      className="secondary"
                      disabled={auditPage >= auditPageCount || !selectedOrgId || loadingAudit}
                      onClick={() => selectedOrgId && governanceToken && loadAuditPage(governanceToken, selectedOrgId, auditPage + 1)}
                    >
                      Next
                    </button>
                  </div>
                ) : null}
              </div>
            </article>
          </section>
        </>
      )}

      {errorGovernance ? <p className="error">{errorGovernance}</p> : null}
    </>
  );
}
