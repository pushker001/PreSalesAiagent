import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchLeadQualification, fetchLeads } from "../lib/api";
import { formatDate, titleFromAction, toneFromAction } from "../lib/formatters";
import {
  EmptyState,
  LoadingState,
  MetricCard,
  ScoreBadge,
  SectionHeader,
  StatusPill,
  Surface,
} from "../components/ui";

function deriveMetrics(leads, qualifications) {
  const total = leads.length;
  const qualified = qualifications.filter((item) => item?.overall_score >= 55).length;
  const followUp = qualifications.filter((item) => item?.recommended_action === "follow_up").length;
  const booked = leads.filter((lead) => lead.status === "booked").length;
  const averageScore = qualifications.length
    ? Math.round(
        qualifications.reduce((sum, item) => sum + (item?.overall_score || 0), 0) / qualifications.length,
      )
    : 0;

  return { total, qualified, followUp, booked, averageScore };
}

export default function DashboardPage() {
  const [leads, setLeads] = useState([]);
  const [qualificationMap, setQualificationMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError("");

      try {
        const leadItems = await fetchLeads();
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

  const qualifications = leads.map((lead) => qualificationMap[lead.id]).filter(Boolean);
  const metrics = deriveMetrics(leads, qualifications);
  const priorityLeads = [...leads]
    .sort(
      (a, b) =>
        (qualificationMap[b.id]?.overall_score || 0) - (qualificationMap[a.id]?.overall_score || 0),
    )
    .slice(0, 3);

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
        <MetricCard label="Total leads" value={metrics.total} detail="All saved opportunities" />
        <MetricCard label="Qualified" value={metrics.qualified} detail="Score 55 or above" tone="good" />
        <MetricCard label="Needs follow-up" value={metrics.followUp} detail="Recommended next action" tone="warm" />
        <MetricCard label="Booked" value={metrics.booked} detail="Lead status booked" />
        <MetricCard
          label="Average score"
          value={metrics.averageScore}
          detail="Across latest qualifications"
          tone="watch"
        />
      </div>

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
