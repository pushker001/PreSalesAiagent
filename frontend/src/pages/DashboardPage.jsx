import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  approveAgentAction,
  dismissAgentAction,
  fetchAgentActions,
  fetchDashboardMetrics,
  fetchLeads,
  fetchLeadQualification,
  markAgentActionSent,
} from "../lib/api";
import { formatDate, titleFromAction, toneFromAction } from "../lib/formatters";
import ActionCard from "../components/ActionCard";
import {
  EmptyState,
  LoadingState,
  MetricCard,
  ScoreBadge,
  SectionHeader,
  StatusPill,
  Surface,
} from "../components/ui";


export default function DashboardPage() {
  const [leads, setLeads] = useState([]);
  const [qualificationMap, setQualificationMap] = useState({});
  const [dashboardMetrics, setDashboardMetrics] = useState(null);
  const [agentActions, setAgentActions] = useState([]);
  const [actionBusyId, setActionBusyId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");

  async function fetchOpenAgentActions() {
    const [pendingActions, approvedActions] = await Promise.all([
      fetchAgentActions("pending_review").catch(() => []),
      fetchAgentActions("approved").catch(() => []),
    ]);

    return [...(pendingActions || []), ...(approvedActions || [])];
  }

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError("");

      try {
        const [leadItems, metricsData, openActions] = await Promise.all([
          fetchLeads(),
          fetchDashboardMetrics().catch(() => null),
          fetchOpenAgentActions(),
        ]);

        const qualifications = await Promise.all(
          leadItems.map(async (lead) => {
            try {
              const qualification = await fetchLeadQualification(lead.id);
              return [lead.id, qualification];
            } catch {
              return [lead.id, null];
            }
          }),
        );

        if (!active) return;

        setLeads(leadItems);
        setDashboardMetrics(metricsData);
        setAgentActions(openActions || []);
        setQualificationMap(Object.fromEntries(qualifications));
      } catch (err) {
        if (!active) return;
        setError(err.message || "Failed to load leads.");
      } finally {
        if (active) setLoading(false);
      }
    }

    load();
    return () => {
      active = false;
    };
  }, []);

  async function refreshAgentActions() {
    const openActions = await fetchOpenAgentActions();
    setAgentActions(openActions || []);
  }

  async function handleActionMutation(actionId, mutation) {
    setActionBusyId(actionId);
    setActionError("");

    try {
      await mutation(actionId);
      await refreshAgentActions();
    } catch (err) {
      setActionError(err.message || "Failed to update agent action.");
    } finally {
      setActionBusyId("");
    }
  }

  if (loading) {
    return <LoadingState title="Loading dashboard" body="Gathering lead activity and qualification signals." />;
  }

  if (error) {
    return (
      <EmptyState
        title="Dashboard unavailable"
        body={error}
        action={
          <Link className="button button-primary" to="/analyze">
            Analyze a new lead
          </Link>
        }
      />
    );
  }

  if (!leads.length) {
    return (
      <EmptyState
        title="No leads in the workspace yet"
        body="Run your first analysis to start building a pipeline of coach-ready lead intelligence."
        action={
          <Link className="button button-primary" to="/analyze">
            Analyze your first lead
          </Link>
        }
      />
    );
  }

  const priorityLeads = [...leads]
    .sort(
      (a, b) =>
        (qualificationMap[b.id]?.overall_score || 0) - (qualificationMap[a.id]?.overall_score || 0),
    )
    .slice(0, 3);
  const isHighPriorityAction = (action) => {
    const priority = String(action.priority || "").toLowerCase();
    return priority === "high" || priority === "urgent";
  };

  const isScheduledForLater = (action) => {
    if (!action.due_at) return false;
    return new Date(action.due_at).getTime() > Date.now();
  };

  const scheduledActions = agentActions.filter(isScheduledForLater);
  const currentActions = agentActions.filter((action) => !isScheduledForLater(action));
  const highPriorityActions = currentActions.filter(isHighPriorityAction);
  const standardPriorityActions = currentActions.filter((action) => !isHighPriorityAction(action));

  return (
    <div className="page-stack">
      <Surface className="hero-panel">
        <div>
          <p className="eyebrow">Coach pipeline command</p>
          <h1>Know exactly which lead deserves your attention next.</h1>
          <p className="hero-copy">
            Your dashboard blends AI-generated intelligence, qualification, and next-step guidance
            so you can move from preparation to action without hesitation.
          </p>
        </div>
        <div className="hero-actions">
          <Link className="button button-primary" to="/analyze">
            Launch new analysis
          </Link>
          <div className="signal-chip">
            <span className="signal-dot" />
            Retrieval layer is live
          </div>
        </div>
      </Surface>

      <div className="metrics-grid">
        <MetricCard label="Total leads" value={leads.length} detail="All saved opportunities" />
        <MetricCard label="Avg score" value={dashboardMetrics?.average_qualification_score ?? "—"} detail="Across all qualifications" tone="watch" />
        <MetricCard label="Booked" value={dashboardMetrics?.qualification_to_booking.booked ?? "—"} detail="Lead status booked" tone="good" />
        <MetricCard label="Booking rate" value={`${dashboardMetrics?.qualification_to_booking.rate_percent ?? 0}%`} detail="Qualified to booked" tone="warm" />
        <MetricCard label="AI actions" value={dashboardMetrics?.ai_actions_count ?? "—"} detail="Suggestions generated" />
      </div>

      {dashboardMetrics?.stagnant_leads?.length ? (
        <Surface>
          <SectionHeader
            eyebrow="Attention needed"
            title="Stagnant leads"
            subtitle="No activity in the last 7 days and still open."
          />
          <div className="recent-list">
            {dashboardMetrics.stagnant_leads.map((lead) => (
              <Link className="recent-item" key={lead.id} to={`/leads/${lead.id}`}>
                <div>
                  <strong>{lead.client_name}</strong>
                  <p>{lead.status}</p>
                </div>
                <span>{lead.last_activity_at ? formatDate(lead.last_activity_at) : "No activity"}</span>
              </Link>
            ))}
          </div>
        </Surface>
      ) : null}

      {dashboardMetrics?.pipeline_breakdown ? (
        <Surface>
          <SectionHeader eyebrow="Pipeline" title="Leads by status" subtitle="Current distribution of leads across all stages." />
          <div className="metrics-grid">
            {Object.entries(dashboardMetrics.pipeline_breakdown).map(([status, count]) => (
              <MetricCard key={status} label={status} value={count} detail="leads" />
            ))}
          </div>
        </Surface>
      ) : null}

      <Surface>
        <SectionHeader
          eyebrow="Agent actions"
          title="Action inbox"
          subtitle="AI-created sales actions waiting for coach review."
        />

        {actionError ? <div className="inline-error">{actionError}</div> : null}

        {agentActions.length ? (
          <div className="action-inbox-list">
            {highPriorityActions.length > 0 && (
              <div className="action-group">
                <h4 style={{ color: "var(--tone-warm-text)", marginBottom: "1rem" }}>Requires immediate attention</h4>
                {highPriorityActions.map((action) => {
                  const lead = leads.find(l => l.id === action.lead_id);
                  const qualification = qualificationMap[action.lead_id];
                  return (
                    <ActionCard 
                      key={action.id}
                      action={action}
                      lead={lead}
                      qualification={qualification}
                      actionBusyId={actionBusyId}
                      onApprove={(id) => handleActionMutation(id, approveAgentAction)}
                      onMarkSent={(id) => handleActionMutation(id, markAgentActionSent)}
                      onDismiss={(id) => handleActionMutation(id, dismissAgentAction)}
                    />
                  );
                })}
              </div>
            )}
            
            {standardPriorityActions.length > 0 && (
              <div className="action-group">
                <h4 style={{ marginTop: "1.5rem", marginBottom: "1rem" }}>Standard priority</h4>
                {standardPriorityActions.map((action) => {
                  const lead = leads.find(l => l.id === action.lead_id);
                  const qualification = qualificationMap[action.lead_id];
                  return (
                    <ActionCard 
                      key={action.id}
                      action={action}
                      lead={lead}
                      qualification={qualification}
                      actionBusyId={actionBusyId}
                      onApprove={(id) => handleActionMutation(id, approveAgentAction)}
                      onMarkSent={(id) => handleActionMutation(id, markAgentActionSent)}
                      onDismiss={(id) => handleActionMutation(id, dismissAgentAction)}
                    />
                  );
                })}
              </div>
            )}

            {scheduledActions.length > 0 && (
              <div className="action-group">
                <h4 style={{ marginTop: "1.5rem", marginBottom: "1rem" }}>Scheduled for later</h4>
                {scheduledActions.map((action) => {
                  const lead = leads.find(l => l.id === action.lead_id);
                  const qualification = qualificationMap[action.lead_id];
                  return (
                    <ActionCard 
                      key={action.id}
                      action={action}
                      lead={lead}
                      qualification={qualification}
                      actionBusyId={actionBusyId}
                      onApprove={(id) => handleActionMutation(id, approveAgentAction)}
                      onMarkSent={(id) => handleActionMutation(id, markAgentActionSent)}
                      onDismiss={(id) => handleActionMutation(id, dismissAgentAction)}
                    />
                  );
                })}
              </div>
            )}
          </div>
        ) : (
          <EmptyState
            title="No pending actions"
            body="When agents create sales actions, they will appear here for review."
          />
        )}
      </Surface>

      <div className="split-layout">
        <Surface>
          <SectionHeader
            eyebrow="Priority"
            title="High-attention leads"
            subtitle="The strongest opportunities based on the latest qualification signals."
          />
          <div className="priority-list">
            {priorityLeads.map((lead) => {
              const qualification = qualificationMap[lead.id];
              return (
                <Link className="priority-item" key={lead.id} to={`/leads/${lead.id}`}>
                  <div>
                    <div className="priority-head">
                      <strong>{lead.client_name}</strong>
                      <StatusPill tone={toneFromAction(qualification?.recommended_action)}>
                        {qualification ? titleFromAction(qualification.recommended_action) : "No qualification"}
                      </StatusPill>
                    </div>
                    <p>{lead.problem_mentioned || "No explicit problem captured yet."}</p>
                    <small>{lead.website_url || "Website not provided"}</small>
                  </div>
                  <ScoreBadge
                    label="Score"
                    score={qualification?.overall_score || 0}
                  />
                </Link>
              );
            })}
          </div>
        </Surface>

        <Surface>
          <SectionHeader
            eyebrow="Recent activity"
            title="Freshly analyzed leads"
            subtitle="Open a lead to review the report, scripts, and qualification outcome."
          />
          <div className="recent-list">
            {leads.slice(0, 5).map((lead) => {
              const qualification = qualificationMap[lead.id];
              return (
                <Link className="recent-item" key={lead.id} to={`/leads/${lead.id}`}>
                  <div>
                    <strong>{lead.client_name}</strong>
                    <p>
                      {lead.client_type} · {lead.lead_temperature}
                    </p>
                  </div>
                  <div className="recent-meta">
                    <span>{formatDate(lead.updated_at)}</span>
                    {qualification ? <ScoreBadge label="Q" score={qualification.overall_score} /> : null}
                  </div>
                </Link>
              );
            })}
          </div>
        </Surface>
      </div>

      <Surface>
        <SectionHeader
          eyebrow="Pipeline"
          title="Lead workspace"
          subtitle="A clean list your frontend can grow into filtering, sorting, and pipeline actions."
        />
        <div className="table-shell">
          <table className="data-table">
            <thead>
              <tr>
                <th>Lead</th>
                <th>Status</th>
                <th>Stage</th>
                <th>Qualification</th>
                <th>Recommended action</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {leads.map((lead) => {
                const qualification = qualificationMap[lead.id];
                return (
                  <tr key={lead.id}>
                    <td>
                      <Link className="table-link" to={`/leads/${lead.id}`}>
                        {lead.client_name}
                      </Link>
                      <small>{lead.website_url || lead.client_type}</small>
                    </td>
                    <td>
                      <StatusPill>{lead.status}</StatusPill>
                    </td>
                    <td>{lead.revenue_stage}</td>
                    <td>{qualification ? qualification.overall_score : "—"}</td>
                    <td>
                      {qualification ? (
                        <StatusPill tone={toneFromAction(qualification.recommended_action)}>
                          {titleFromAction(qualification.recommended_action)}
                        </StatusPill>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td>{formatDate(lead.updated_at)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Surface>
    </div>
  );
}
