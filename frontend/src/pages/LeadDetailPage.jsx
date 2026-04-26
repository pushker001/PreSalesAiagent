import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  fetchLead,
  fetchLeadQualification,
  fetchLeadReports,
  updateLead,
} from "../lib/api";
import { formatDate, titleFromAction, toneFromAction } from "../lib/formatters";
import {
  CopyBlock,
  EmptyState,
  LoadingState,
  ScoreBadge,
  SectionHeader,
  StatusPill,
  Surface,
} from "../components/ui";

function TabButton({ active, children, onClick }) {
  return (
    <button className={`tab-button${active ? " is-active" : ""}`} onClick={onClick} type="button">
      {children}
    </button>
  );
}

export default function LeadDetailPage() {
  const { leadId } = useParams();
  const [lead, setLead] = useState(null);
  const [reports, setReports] = useState([]);
  const [qualification, setQualification] = useState(null);
  const [selectedReportId, setSelectedReportId] = useState(null);
  const [tab, setTab] = useState("overview");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [leadStateForm, setLeadStateForm] = useState({
    status: "",
    booking_status: "",
    coach_notes: "",
  });
  const [saveState, setSaveState] = useState({ saving: false, error: "", success: "" });

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError("");
      try {
        const [leadData, reportData, qualificationData] = await Promise.all([
          fetchLead(leadId),
          fetchLeadReports(leadId),
          fetchLeadQualification(leadId),
        ]);

        if (!active) return;

        setLead(leadData);
        setReports(reportData);
        setQualification(qualificationData);
        setSelectedReportId(reportData[0]?.id || null);
        setLeadStateForm({
          status: leadData.status || "",
          booking_status: leadData.booking_status || "",
          coach_notes: leadData.coach_notes || "",
        });
      } catch (err) {
        if (!active) return;
        setError(err.message || "Failed to load lead workspace.");
      } finally {
        if (active) setLoading(false);
      }
    }

    load();
    return () => {
      active = false;
    };
  }, [leadId]);

  function handleLeadStateChange(event) {
    const { name, value } = event.target;
    setLeadStateForm((current) => ({ ...current, [name]: value }));
    setSaveState((current) => ({ ...current, success: "", error: "" }));
  }

  async function handleLeadStateSave(event) {
    event.preventDefault();
    setSaveState({ saving: true, error: "", success: "" });

    try {
      const updatedLead = await updateLead(leadId, {
        status: leadStateForm.status || undefined,
        booking_status: leadStateForm.booking_status || undefined,
        coach_notes: leadStateForm.coach_notes.trim() || undefined,
        last_activity_at: new Date().toISOString(),
      });

      setLead(updatedLead);
      setLeadStateForm({
        status: updatedLead.status || "",
        booking_status: updatedLead.booking_status || "",
        coach_notes: updatedLead.coach_notes || "",
      });
      setSaveState({ saving: false, error: "", success: "Lead state updated." });
    } catch (err) {
      setSaveState({
        saving: false,
        error: err.message || "Failed to update lead state.",
        success: "",
      });
    }
  }

  if (loading) {
    return <LoadingState title="Loading lead workspace" body="Gathering saved reports and qualification context." />;
  }

  if (error || !lead) {
    return (
      <EmptyState
        title="Lead unavailable"
        body={error || "We couldn't find that lead."}
        action={
          <Link className="button button-primary" to="/dashboard">
            Back to dashboard
          </Link>
        }
      />
    );
  }

  const selectedReport = reports.find((item) => item.id === selectedReportId) || reports[0] || null;
  const reportPayload = selectedReport?.full_report_json || {};
  const scripts = reportPayload.scripts || {};
  const synthesis = reportPayload.synthesis || {};

  return (
    <div className="page-stack">
      <Surface className="lead-header">
        <div>
          <p className="eyebrow">Lead workspace</p>
          <h1>{lead.client_name}</h1>
          <p className="section-subtitle">
            {lead.client_type} · {lead.revenue_stage} · {lead.lead_temperature}
          </p>
          <div className="tag-cloud">
            <StatusPill>{lead.status}</StatusPill>
            {lead.website_url ? <StatusPill tone="default">{lead.website_url}</StatusPill> : null}
            {qualification ? (
              <StatusPill tone={toneFromAction(qualification.recommended_action)}>
                {titleFromAction(qualification.recommended_action)}
              </StatusPill>
            ) : null}
          </div>
        </div>
        <div className="result-summary-meta">
          {qualification ? (
            <ScoreBadge label="Qualification" score={qualification.overall_score || 0} />
          ) : null}
          {selectedReport ? (
            <ScoreBadge label="Intelligence" score={selectedReport.intelligence_score || 0} />
          ) : null}
        </div>
      </Surface>

      <div className="split-layout">
        <Surface>
          <SectionHeader title="Decision snapshot" subtitle="The current recommendation for this lead." />
          {qualification ? (
            <div className="qualification-panel">
              <div className="qualification-card">
                <ScoreBadge label="Overall score" score={qualification.overall_score || 0} />
                <StatusPill tone={toneFromAction(qualification.recommended_action)}>
                  {titleFromAction(qualification.recommended_action)}
                </StatusPill>
              </div>
              <p className="hero-copy">{qualification.reasoning}</p>
            </div>
          ) : (
            <p className="section-subtitle">No qualification record found yet.</p>
          )}
        </Surface>

        <Surface>
          <SectionHeader title="Report history" subtitle="Switch between saved reports for this lead." />
          {reports.length ? (
            <div className="report-history-list">
              {reports.map((report) => (
                <button
                  className={`history-item${selectedReportId === report.id ? " is-active" : ""}`}
                  key={report.id}
                  onClick={() => setSelectedReportId(report.id)}
                  type="button"
                >
                  <div>
                    <strong>{formatDate(report.generated_at)}</strong>
                    <small>Saved report</small>
                  </div>
                  <ScoreBadge label="Score" score={report.intelligence_score || 0} />
                </button>
              ))}
            </div>
          ) : (
            <p className="section-subtitle">No report history available.</p>
          )}
        </Surface>
      </div>

      <Surface>
        <SectionHeader
          title="Lead state controls"
          subtitle="Capture coach notes and manage the live sales state for this opportunity."
        />

        <form className="lead-state-form" onSubmit={handleLeadStateSave}>
          <div className="field-grid">
            <label className="field">
              <span>Status</span>
              <select name="status" onChange={handleLeadStateChange} value={leadStateForm.status}>
                <option value="new">New</option>
                <option value="analyzed">Analyzed</option>
                <option value="qualified">Qualified</option>
                <option value="nurture">Nurture</option>
                <option value="booked">Booked</option>
                <option value="closed_won">Closed Won</option>
                <option value="closed_lost">Closed Lost</option>
              </select>
            </label>

            <label className="field">
              <span>Booking status</span>
              <select
                name="booking_status"
                onChange={handleLeadStateChange}
                value={leadStateForm.booking_status}
              >
                <option value="">Not set</option>
                <option value="not_started">Not started</option>
                <option value="link_sent">Link sent</option>
                <option value="pending_confirmation">Pending confirmation</option>
                <option value="confirmed">Confirmed</option>
                <option value="completed">Completed</option>
                <option value="no_show">No show</option>
              </select>
            </label>
          </div>

          <label className="field">
            <span>Coach notes</span>
            <textarea
              name="coach_notes"
              onChange={handleLeadStateChange}
              placeholder="Capture what happened on the call, objections, decision timing, or next move."
              rows="5"
              value={leadStateForm.coach_notes}
            />
          </label>

          <div className="lead-state-actions">
            <button className="button button-primary" disabled={saveState.saving} type="submit">
              {saveState.saving ? "Saving…" : "Save lead state"}
            </button>
            {lead.last_activity_at ? (
              <span className="lead-state-meta">Last activity: {formatDate(lead.last_activity_at)}</span>
            ) : null}
          </div>

          {saveState.error ? <div className="inline-error">{saveState.error}</div> : null}
          {saveState.success ? <div className="inline-success">{saveState.success}</div> : null}
        </form>
      </Surface>

      <Surface>
        <div className="tabs-row">
          <TabButton active={tab === "overview"} onClick={() => setTab("overview")}>
            Overview
          </TabButton>
          <TabButton active={tab === "scripts"} onClick={() => setTab("scripts")}>
            Scripts
          </TabButton>
          <TabButton active={tab === "timeline"} onClick={() => setTab("timeline")}>
            Timeline
          </TabButton>
        </div>

        {tab === "overview" ? (
          <div className="overview-grid">
            <Surface className="inner-surface">
              <SectionHeader title="Lead context" />
              <div className="detail-list">
                <div>
                  <span>Lead source</span>
                  <strong>{lead.lead_source}</strong>
                </div>
                <div>
                  <span>Problem mentioned</span>
                  <strong>{lead.problem_mentioned || "No explicit pain captured"}</strong>
                </div>
                <div>
                  <span>Offer</span>
                  <strong>
                    {lead.offer_type} · {lead.coach_offer_price_range}
                  </strong>
                </div>
              </div>
            </Surface>

            <Surface className="inner-surface">
              <SectionHeader title="Latest intelligence" />
              <p className="hero-copy">{synthesis.company_summary || "No summary available yet."}</p>
              <div className="tag-cloud">
                {(synthesis.personalization_hooks || []).map((item) => (
                  <StatusPill key={item} tone="watch">
                    {item}
                  </StatusPill>
                ))}
              </div>
            </Surface>
          </div>
        ) : null}

        {tab === "scripts" ? (
          <div className="report-grid">
            <CopyBlock label="Opening line" content={scripts.opening} />
            <CopyBlock label="Discovery questions" content={scripts.discovery_questions || []} />
            <CopyBlock label="Value proposition" content={scripts.value_proposition} />
            <CopyBlock label="Closing lines" content={scripts.closing_lines} />
          </div>
        ) : null}

        {tab === "timeline" ? (
          <div className="timeline-list">
            <div className="timeline-card">
              <span className="eyebrow">Analyzed</span>
              <strong>{selectedReport ? formatDate(selectedReport.generated_at) : "Unknown"}</strong>
              <p>Latest AI report saved and attached to this lead.</p>
            </div>
            <div className="timeline-card">
              <span className="eyebrow">Qualified</span>
              <strong>{qualification ? titleFromAction(qualification.recommended_action) : "Pending"}</strong>
              <p>{qualification?.reasoning || "Qualification history will expand here as memory features are added."}</p>
            </div>
            <div className="timeline-card">
              <span className="eyebrow">Future memory</span>
              <strong>Notes, calls, follow-up, booking</strong>
              <p>This section is intentionally prepared for the next modules.</p>
            </div>
          </div>
        ) : null}
      </Surface>
    </div>
  );
}
