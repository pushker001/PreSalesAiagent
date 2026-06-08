import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  createLeadActivity,
  fetchLead,
  fetchLeadActivities,
  fetchLeadQualification,
  fetchLeadReports,
  generateBookingSuggestion,
  generateConversationSuggestion,
  generateFollowUp,
  markBookingLinkSent,
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

const ACTIVITY_TYPE_OPTIONS = [
  {
    value: "call_logged",
    label: "Call logged",
    title: "Call logged",
    placeholder: "Summarize what happened on the call, key objections, and the agreed next step.",
  },
  {
    value: "follow_up_sent",
    label: "Follow-up sent",
    title: "Follow-up sent",
    placeholder: "Capture what follow-up you sent and the angle you used.",
  },
  {
    value: "follow_up_replied",
    label: "Follow-up replied",
    title: "Lead replied to follow-up",
    placeholder: "Summarize what the lead said and what it means for the next move.",
  },
  {
    value: "proposal_sent",
    label: "Proposal sent",
    title: "Proposal sent",
    placeholder: "Note what offer or proposal was sent and any timing attached to it.",
  },
  {
    value: "booking_reminder_sent",
    label: "Booking reminder",
    title: "Booking reminder sent",
    placeholder: "Describe the reminder that was sent and what action you're waiting on.",
  },
  {
    value: "general_note",
    label: "General note",
    title: "General timeline note",
    placeholder: "Add any other important memory you want this lead timeline to retain.",
  },
];

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
  const [activities, setActivities] = useState([]);
  const [activityForm, setActivityForm] = useState({
    event_type: ACTIVITY_TYPE_OPTIONS[0].value,
    title: ACTIVITY_TYPE_OPTIONS[0].title,
    details: "",
  });
  const [activitySave, setActivitySave] = useState({ saving: false, error: "", success: "" });
  const [followUpState, setFollowUpState] = useState({
    loading: false,
    error: "",
    suggestion: null,
  });
  const [bookingState, setBookingState] = useState({
    loading: false,
    error: "",
    suggestion: null,
  });
  const [linkSentState, setLinkSentState] = useState({ saving: false, error: "", success: "" });
  const [conversationState, setConversationState] = useState({
    currentMessage: "",
    loading: false,
    error: "",
    suggestion: null,
  });

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError("");
      try {
        const [leadData, reportData, qualificationData, activitiesData] = await Promise.all([
          fetchLead(leadId),
          fetchLeadReports(leadId),
          fetchLeadQualification(leadId),
          fetchLeadActivities(leadId).catch(() => []),
        ]);

        if (!active) return;

        setLead(leadData);
        setReports(reportData);
        setQualification(qualificationData);
        setSelectedReportId(reportData[0]?.id || null);
        setActivities(activitiesData || []);
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

  function handleActivityTypeChange(event) {
    const nextType = ACTIVITY_TYPE_OPTIONS.find((item) => item.value === event.target.value);
    setActivityForm((current) => ({
      ...current,
      event_type: event.target.value,
      title: nextType?.title || current.title,
    }));
    setActivitySave((current) => ({ ...current, success: "", error: "" }));
  }

  function handleActivityFieldChange(event) {
    const { name, value } = event.target;
    setActivityForm((current) => ({ ...current, [name]: value }));
    setActivitySave((current) => ({ ...current, success: "", error: "" }));
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
      const refreshedActivities = await fetchLeadActivities(leadId).catch(() => []);

      setLead(updatedLead);
      setActivities(refreshedActivities);
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

  async function handleActivitySave(event) {
    event.preventDefault();
    setActivitySave({ saving: true, error: "", success: "" });

    try {
      const createdActivity = await createLeadActivity(leadId, {
        event_type: activityForm.event_type,
        title: activityForm.title.trim(),
        details: activityForm.details.trim() || null,
        metadata_json: {
          source: "coach",
          category: activityForm.event_type,
        },
      });

      setActivities((current) => [createdActivity, ...current]);
      const selectedType = ACTIVITY_TYPE_OPTIONS.find((item) => item.value === activityForm.event_type);
      setActivityForm({
        event_type: activityForm.event_type,
        title: selectedType?.title || "",
        details: "",
      });
      setActivitySave({ saving: false, error: "", success: "Timeline event added." });
    } catch (err) {
      setActivitySave({
        saving: false,
        error: err.message || "Failed to save timeline event.",
        success: "",
      });
    }
  }

  async function handleGenerateFollowUp() {
    setFollowUpState({ loading: true, error: "", suggestion: null });

    try {
      const suggestion = await generateFollowUp(leadId);
      setFollowUpState({ loading: false, error: "", suggestion });
    } catch (err) {
      setFollowUpState({
        loading: false,
        error: err.message || "Failed to generate follow-up suggestion.",
        suggestion: null,
      });
    }
  }

  async function handleMarkLinkSent() {
    setLinkSentState({ saving: true, error: "", success: "" });
    try {
      const updatedLead = await markBookingLinkSent(leadId);
      const refreshedActivities = await fetchLeadActivities(leadId).catch(() => activities);
      setLead(updatedLead);
      setActivities(refreshedActivities);
      setLeadStateForm((current) => ({ ...current, booking_status: updatedLead.booking_status || "" }));
      setLinkSentState({ saving: false, error: "", success: "Booking link marked as sent." });
    } catch (err) {
      setLinkSentState({ saving: false, error: err.message || "Failed to mark link sent.", success: "" });
    }
  }

  async function handleGenerateBookingSuggestion() {
    setBookingState({ loading: true, error: "", suggestion: null });

    try {
      const suggestion = await generateBookingSuggestion(leadId);
      setBookingState({ loading: false, error: "", suggestion });
    } catch (err) {
      setBookingState({
        loading: false,
        error: err.message || "Failed to generate booking suggestion.",
        suggestion: null,
      });
    }
  }

  function handleConversationMessageChange(event) {
    const { value } = event.target;
    setConversationState((current) => ({
      ...current,
      currentMessage: value,
      error: "",
    }));
  }

  async function handleGenerateConversationSuggestion() {
    if (!conversationState.currentMessage.trim()) {
      setConversationState((current) => ({
        ...current,
        error: "Add the lead's latest message before generating a reply.",
      }));
      return;
    }

    setConversationState((current) => ({
      ...current,
      loading: true,
      error: "",
      suggestion: null,
    }));

    try {
      const suggestion = await generateConversationSuggestion(leadId, conversationState.currentMessage.trim());
      const refreshedActivities = await fetchLeadActivities(leadId).catch(() => activities);
      setActivities(refreshedActivities);
      setConversationState((current) => ({
        ...current,
        loading: false,
        error: "",
        suggestion,
      }));
    } catch (err) {
      setConversationState((current) => ({
        ...current,
        loading: false,
        error: err.message || "Failed to generate conversation suggestion.",
        suggestion: null,
      }));
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
  const activeActivityOption =
    ACTIVITY_TYPE_OPTIONS.find((item) => item.value === activityForm.event_type) || ACTIVITY_TYPE_OPTIONS[0];

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
            {lead.email ? <StatusPill tone="default">{lead.email}</StatusPill> : null}
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
                <option value="reminder_sent">Reminder sent</option>
                <option value="confirmed">Confirmed</option>
                <option value="completed">Completed</option>
                <option value="no_show">No show</option>
                <option value="abandoned">Abandoned</option>
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
          <TabButton active={tab === "follow-up"} onClick={() => setTab("follow-up")}>
            Follow-up
          </TabButton>
          <TabButton active={tab === "booking"} onClick={() => setTab("booking")}>
            Booking
          </TabButton>
          <TabButton active={tab === "conversation"} onClick={() => setTab("conversation")}>
            Conversation
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

        {tab === "follow-up" ? (
          <div className="follow-up-stack">
            <Surface className="inner-surface">
              <SectionHeader
                title="Follow-up agent"
                subtitle="Generate the next best follow-up based on qualification, memory, and current lead state."
              />

              <div className="follow-up-actions">
                <button
                  className="button button-primary"
                  disabled={followUpState.loading}
                  onClick={handleGenerateFollowUp}
                  type="button"
                >
                  {followUpState.loading ? "Generating…" : "Generate follow-up"}
                </button>

                {qualification ? (
                  <StatusPill tone={toneFromAction(qualification.recommended_action)}>
                    {titleFromAction(qualification.recommended_action)}
                  </StatusPill>
                ) : null}
              </div>

              {followUpState.error ? <div className="inline-error">{followUpState.error}</div> : null}
            </Surface>

            {followUpState.suggestion ? (
              <div className="follow-up-grid">
                <Surface className="inner-surface">
                  <SectionHeader title="Suggestion summary" subtitle="Why this follow-up was chosen right now." />
                  <div className="detail-list">
                    <div>
                      <span>Follow-up type</span>
                      <strong>{followUpState.suggestion.follow_up_type}</strong>
                    </div>
                    <div>
                      <span>Recommended timing</span>
                      <strong>{followUpState.suggestion.recommended_timing}</strong>
                    </div>
                  </div>
                  <p className="hero-copy">{followUpState.suggestion.reasoning}</p>
                </Surface>

                <CopyBlock label={`Subject line: ${followUpState.suggestion.subject_line}`} content={followUpState.suggestion.message} />
              </div>
            ) : (
              <Surface className="inner-surface">
                <EmptyState
                  title="No follow-up generated yet"
                  body="Generate a suggestion to see the recommended follow-up type, timing, and ready-to-use message."
                />
              </Surface>
            )}
          </div>
        ) : null}

        {tab === "booking" ? (
          <div className="follow-up-stack">
            <Surface className="inner-surface">
              <SectionHeader
                title="Booking agent"
                subtitle="Generate the next best booking push based on qualification, booking state, and recent lead momentum."
              />

              <div className="follow-up-actions">
                <button
                  className="button button-primary"
                  disabled={bookingState.loading}
                  onClick={handleGenerateBookingSuggestion}
                  type="button"
                >
                  {bookingState.loading ? "Generating…" : "Generate booking suggestion"}
                </button>

                {lead.booking_status ? (
                  <StatusPill tone="watch">{lead.booking_status}</StatusPill>
                ) : null}
              </div>

              {bookingState.error ? <div className="inline-error">{bookingState.error}</div> : null}
            </Surface>

            {bookingState.suggestion ? (
              <div className="follow-up-grid">
                <Surface className="inner-surface">
                  <SectionHeader title="Booking strategy" subtitle="Why the booking agent chose this push." />
                  <div className="detail-list">
                    <div>
                      <span>Should push booking</span>
                      <strong>{bookingState.suggestion.should_push_booking ? "Yes" : "Not yet"}</strong>
                    </div>
                    <div>
                      <span>Booking mode</span>
                      <strong>{bookingState.suggestion.booking_mode}</strong>
                    </div>
                    <div>
                      <span>Recommended timing</span>
                      <strong>{bookingState.suggestion.recommended_timing}</strong>
                    </div>
                    <div>
                      <span>Suggested CTA</span>
                      <strong>{bookingState.suggestion.suggested_cta}</strong>
                    </div>
                    {bookingState.suggestion.booking_url ? (
                      <div>
                        <span>Booking link</span>
                        <strong>{bookingState.suggestion.booking_url}</strong>
                      </div>
                    ) : null}
                  </div>
                  <p className="hero-copy">{bookingState.suggestion.reasoning}</p>
                </Surface>

                <CopyBlock
                  label={`Subject line: ${bookingState.suggestion.subject_line}`}
                  content={bookingState.suggestion.message}
                />

                <Surface className="inner-surface">
                  <SectionHeader
                    title="Mark as sent"
                    subtitle="Once you've sent the booking message, mark it here to update the lead state and log it to the timeline."
                  />
                  <div className="follow-up-actions">
                    <button
                      className="button button-primary"
                      disabled={linkSentState.saving || lead.booking_status === "link_sent"}
                      onClick={handleMarkLinkSent}
                      type="button"
                    >
                      {linkSentState.saving ? "Saving…" : lead.booking_status === "link_sent" ? "Link already marked sent" : "Mark link as sent"}
                    </button>
                    {lead.booking_status ? <StatusPill tone="watch">{lead.booking_status}</StatusPill> : null}
                  </div>
                  {linkSentState.error ? <div className="inline-error">{linkSentState.error}</div> : null}
                  {linkSentState.success ? <div className="inline-success">{linkSentState.success}</div> : null}
                </Surface>
              </div>
            ) : (
              <Surface className="inner-surface">
                <EmptyState
                  title="No booking suggestion generated yet"
                  body="Generate a booking strategy to see whether the lead should be pushed toward scheduling right now."
                />
              </Surface>
            )}
          </div>
        ) : null}

        {tab === "conversation" ? (
          <div className="follow-up-stack">
            <Surface className="inner-surface">
              <SectionHeader
                title="Conversation agent"
                subtitle="Paste what the lead just said and generate a context-aware reply for the coach to use live."
              />

              <div className="lead-state-form">
                <label className="field">
                  <span>
                    Latest lead message
                    <small>Use the exact objection, hesitation, or reply you want help with.</small>
                  </span>
                  <textarea
                    className="conversation-textarea"
                    onChange={handleConversationMessageChange}
                    placeholder="Example: I need to think about it first before making a decision."
                    value={conversationState.currentMessage}
                  />
                </label>

                <div className="follow-up-actions">
                  <button
                    className="button button-primary"
                    disabled={conversationState.loading}
                    onClick={handleGenerateConversationSuggestion}
                    type="button"
                  >
                    {conversationState.loading ? "Generating…" : "Generate reply"}
                  </button>

                  {qualification ? (
                    <StatusPill tone={toneFromAction(qualification.recommended_action)}>
                      {titleFromAction(qualification.recommended_action)}
                    </StatusPill>
                  ) : null}
                </div>
              </div>

              {conversationState.error ? <div className="inline-error">{conversationState.error}</div> : null}
            </Surface>

            {conversationState.suggestion ? (
              <div className="follow-up-grid">
                <Surface className="inner-surface">
                  <SectionHeader
                    title="Conversation strategy"
                    subtitle="Why the conversation agent chose this reply path."
                  />
                  <div className="detail-list">
                    <div>
                      <span>Reply type</span>
                      <strong>{conversationState.suggestion.reply_type}</strong>
                    </div>
                    <div>
                      <span>Next step</span>
                      <strong>{conversationState.suggestion.next_step}</strong>
                    </div>
                  </div>
                  <p className="hero-copy">{conversationState.suggestion.reasoning}</p>
                </Surface>

                <CopyBlock label="Suggested reply" content={conversationState.suggestion.suggested_reply} />
              </div>
            ) : (
              <Surface className="inner-surface">
                <EmptyState
                  title="No conversation reply generated yet"
                  body="Paste the lead's latest message to get a reply suggestion, next step, and reasoning."
                />
              </Surface>
            )}
          </div>
        ) : null}

        {tab === "timeline" ? (
          <div className="timeline-stack">
            <Surface className="inner-surface">
              <SectionHeader
                title="Log memory event"
                subtitle="Capture calls, follow-ups, proposals, or any other sales context this lead should remember."
              />

              <form className="lead-state-form" onSubmit={handleActivitySave}>
                <div className="field-grid">
                  <label className="field">
                    <span>Activity type</span>
                    <select onChange={handleActivityTypeChange} value={activityForm.event_type}>
                      {ACTIVITY_TYPE_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="field">
                    <span>Timeline title</span>
                    <input
                      name="title"
                      onChange={handleActivityFieldChange}
                      placeholder="What happened?"
                      value={activityForm.title}
                    />
                  </label>
                </div>

                <label className="field">
                  <span>Details</span>
                  <textarea
                    name="details"
                    onChange={handleActivityFieldChange}
                    placeholder={activeActivityOption.placeholder}
                    rows="4"
                    value={activityForm.details}
                  />
                </label>

                <div className="lead-state-actions">
                  <button className="button button-primary" disabled={activitySave.saving} type="submit">
                    {activitySave.saving ? "Saving…" : "Add memory event"}
                  </button>
                </div>

                {activitySave.error ? <div className="inline-error">{activitySave.error}</div> : null}
                {activitySave.success ? <div className="inline-success">{activitySave.success}</div> : null}
              </form>
            </Surface>

            <div className="timeline-list">
              {activities.length ? (
                activities.map((activity) => (
                  <div className="timeline-card" key={activity.id}>
                    <div className="timeline-head">
                      <span className="eyebrow">{activity.event_type}</span>
                      <span className="timeline-date">{formatDate(activity.created_at)}</span>
                    </div>
                    <strong>{activity.title}</strong>
                    <p>{activity.details || "—"}</p>
                  </div>
                ))
              ) : (
                <div className="timeline-card">
                  <span className="eyebrow">No activity yet</span>
                  <strong>Timeline is empty</strong>
                  <p>Activities will appear here as the lead progresses.</p>
                </div>
              )}
            </div>
          </div>
        ) : null}
      </Surface>
    </div>
  );
}
