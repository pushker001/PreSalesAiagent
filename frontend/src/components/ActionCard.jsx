import { Link } from "react-router-dom";
import { StatusPill, ScoreBadge } from "./ui";

export default function ActionCard({
  action,
  lead,
  qualification,
  actionBusyId,
  onApprove,
  onMarkSent,
  onDismiss,
}) {
  const isBusy = actionBusyId === action.id;
  const priority = String(action.priority || "").toLowerCase();
  const isHighPriority = priority === "high" || priority === "urgent";
  const dueAtLabel = action.due_at ? new Date(action.due_at).toLocaleString() : "";

  return (
    <article className="action-card" style={{ marginBottom: "1.5rem" }}>
      <div className="action-card-main">
        <div className="action-card-head">
          <StatusPill tone={isHighPriority ? "warm" : "watch"}>
            {action.priority}
          </StatusPill>
          <StatusPill>{action.status}</StatusPill>
          <span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)", marginLeft: "auto" }}>
            {action.agent_name} Agent
          </span>
        </div>
        
        {/* The Action Output */}
        <h3 style={{ marginTop: "1rem", marginBottom: "0.5rem" }}>{action.title}</h3>
        <div style={{ padding: "1rem", backgroundColor: "var(--surface-sunken)", borderRadius: "6px", marginBottom: "1rem" }}>
          <p style={{ margin: 0, whiteSpace: "pre-wrap" }}>
            {action.message || "No message generated for this action yet."}
          </p>
        </div>
        {action.cta && <p style={{ fontSize: "0.85rem", fontStyle: "italic", color: "var(--text-secondary)", marginBottom: "1rem" }}><strong>CTA:</strong> {action.cta}</p>}

        {/* Lead Context Preview */}
        <div style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: "1rem", marginTop: "1rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
            <h4 style={{ margin: 0, fontSize: "0.9rem" }}>Target: {lead ? lead.client_name : "Unknown"}</h4>
            {qualification && (
              <ScoreBadge score={qualification.overall_score} label="Score" />
            )}
          </div>
          {lead && (
            <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "1rem", display: "flex", flexDirection: "column", gap: "0.25rem" }}>
              <div><strong>Stage:</strong> {lead.revenue_stage || "Unknown"}</div>
              <div><strong>Problem:</strong> {lead.problem_mentioned || "Not identified"}</div>
            </div>
          )}
          <div className="action-card-meta">
            <span>{action.action_type}</span>
            {dueAtLabel ? <span>Due: {dueAtLabel}</span> : null}
            <Link to={`/leads/${action.lead_id}`} style={{ fontWeight: 500 }}>
              View full lead workspace &rarr;
            </Link>
          </div>
        </div>
      </div>

      <div className="action-card-controls">
        <button
          className="button button-primary"
          disabled={isBusy}
          onClick={() => onApprove(action.id)}
          type="button"
        >
          Approve
        </button>
        <button
          className="button button-ghost"
          disabled={isBusy}
          onClick={() => onMarkSent(action.id)}
          type="button"
        >
          Mark sent
        </button>
        <button
          className="button button-ghost"
          disabled={isBusy}
          onClick={() => onDismiss(action.id)}
          type="button"
        >
          Dismiss
        </button>
      </div>
    </article>
  );
}
