import { useState } from "react";
import { Link } from "react-router-dom";
import { analyzeLead } from "../lib/api";
import { titleFromAction, toneFromAction } from "../lib/formatters";
import {
  CopyBlock,
  EmptyState,
  ProgressTimeline,
  ScoreBadge,
  SectionHeader,
  StatusPill,
  Surface,
} from "../components/ui";

const defaults = {
  client_name: "",
  website_url: "",
  linkedin_url: "",
  linkedin_summary: "",
  client_type: "Startup Founder",
  revenue_stage: "Early Stage (<$1M)",
  lead_source: "Inbound",
  lead_temperature: "Warm",
  problem_mentioned: "",
  coach_offer_price_range: "$3k-$10k",
  offer_type: "Strategic Consulting",
  call_goal: "Discovery Call",
};

function Field({ label, children, hint }) {
  return (
    <label className="field">
      <span>
        {label}
        {hint ? <small>{hint}</small> : null}
      </span>
      {children}
    </label>
  );
}

export default function AnalyzeLeadPage() {
  const [form, setForm] = useState(defaults);
  const [result, setResult] = useState(null);
  const [meta, setMeta] = useState(null);
  const [progress, setProgress] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function handleChange(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    setMeta(null);
    setProgress([]);

    try {
      const payload = await analyzeLead(form, {
        onProgress: (item) => setProgress((current) => [...current, item]),
      });

      setResult(payload.closure_report || null);
      setMeta({
        leadId: payload.lead_id,
        reportId: payload.report_id,
        qualification: payload.qualification,
      });
    } catch (err) {
      setError(err.message || "Analysis failed.");
    } finally {
      setLoading(false);
    }
  }

  const synthesis = result?.synthesis || {};
  const scripts = result?.scripts || {};

  return (
    <div className="page-stack">
      <div className="split-layout analyze-layout">
        <Surface className="analysis-form-panel">
          <SectionHeader
            eyebrow="AI workflow"
            title="Analyze a lead before the call"
            subtitle="Capture context once and let the system build intelligence, strategy, scripts, and qualification."
          />

          <form className="analysis-form" onSubmit={handleSubmit}>
            <div className="field-grid">
              <Field label="Client name">
                <input name="client_name" onChange={handleChange} required value={form.client_name} />
              </Field>
              <Field label="Website URL">
                <input name="website_url" onChange={handleChange} value={form.website_url} />
              </Field>
              <Field label="LinkedIn URL">
                <input name="linkedin_url" onChange={handleChange} value={form.linkedin_url} />
              </Field>
              <Field label="Client type">
                <select name="client_type" onChange={handleChange} value={form.client_type}>
                  <option>Solo Founder</option>
                  <option>Agency Owner</option>
                  <option>Startup Founder</option>
                  <option>Enterprise Executive</option>
                  <option>Organization / Association</option>
                </select>
              </Field>
              <Field label="Revenue stage">
                <select name="revenue_stage" onChange={handleChange} value={form.revenue_stage}>
                  <option>Idea Stage</option>
                  <option>Early Stage (&lt;$1M)</option>
                  <option>Scaling ($1M-$5M)</option>
                  <option>Established ($5M+)</option>
                </select>
              </Field>
              <Field label="Lead source">
                <select name="lead_source" onChange={handleChange} value={form.lead_source}>
                  <option>Inbound</option>
                  <option>Outbound</option>
                  <option>Referral</option>
                  <option>Event / Conference</option>
                </select>
              </Field>
              <Field label="Lead temperature">
                <select name="lead_temperature" onChange={handleChange} value={form.lead_temperature}>
                  <option>Cold</option>
                  <option>Warm</option>
                  <option>Hot</option>
                </select>
              </Field>
              <Field label="Offer type">
                <select name="offer_type" onChange={handleChange} value={form.offer_type}>
                  <option>Strategic Consulting</option>
                  <option>High-Ticket Coaching</option>
                  <option>Enterprise Consulting</option>
                </select>
              </Field>
              <Field label="Price range">
                <select
                  name="coach_offer_price_range"
                  onChange={handleChange}
                  value={form.coach_offer_price_range}
                >
                  <option>$3k-$10k</option>
                  <option>$10k-$25k</option>
                  <option>$25k-$50k</option>
                  <option>$50k+</option>
                </select>
              </Field>
              <Field label="Call goal">
                <select name="call_goal" onChange={handleChange} value={form.call_goal}>
                  <option>Discovery Call</option>
                  <option>Sales Call</option>
                  <option>Strategic Partnership / Consulting Qualification</option>
                </select>
              </Field>
            </div>

            <Field label="Problem mentioned">
              <textarea
                name="problem_mentioned"
                onChange={handleChange}
                rows="3"
                value={form.problem_mentioned}
              />
            </Field>
            <Field label="LinkedIn summary" hint="Paste raw profile or company about text">
              <textarea
                name="linkedin_summary"
                onChange={handleChange}
                rows="5"
                value={form.linkedin_summary}
              />
            </Field>

            <button className="button button-primary button-block" disabled={loading} type="submit">
              {loading ? "Running analysis…" : "Run AI analysis"}
            </button>
          </form>
        </Surface>

        <Surface className="analysis-side-panel">
          <SectionHeader
            eyebrow="Live run"
            title="Analysis timeline"
            subtitle="Track the intelligence engine as it moves from research to scripts and qualification."
          />
          {progress.length ? (
            <ProgressTimeline items={progress} />
          ) : (
            <EmptyState
              title="Ready to analyze"
              body="Once you launch a run, the AI workflow will stream progress here in real time."
            />
          )}
          {error ? (
            <div className="inline-error">
              <strong>Run failed</strong>
              <p>{error}</p>
            </div>
          ) : null}
        </Surface>
      </div>

      {result ? (
        <div className="page-stack">
          <Surface className="result-summary">
            <div>
              <p className="eyebrow">Saved result</p>
              <h3>{result.lead_info?.client_name || form.client_name}</h3>
              <p className="section-subtitle">
                Full intelligence report, qualification, and scripts ready for action.
              </p>
            </div>
            <div className="result-summary-meta">
              <ScoreBadge label="Intelligence" score={result.intelligence_score || 0} />
              {meta?.qualification ? (
                <div className="qualification-pill-stack">
                  <ScoreBadge label="Qualification" score={meta.qualification.overall_score || 0} />
                  <StatusPill tone={toneFromAction(meta.qualification.recommended_action)}>
                    {titleFromAction(meta.qualification.recommended_action)}
                  </StatusPill>
                </div>
              ) : null}
            </div>
          </Surface>

          {meta?.leadId ? (
            <Surface className="cta-banner">
              <div>
                <p className="eyebrow">Next move</p>
                <h3>Open the saved lead workspace</h3>
              </div>
              <Link className="button button-primary" to={`/leads/${meta.leadId}`}>
                Open lead detail
              </Link>
            </Surface>
          ) : null}

          <div className="report-grid">
            <Surface>
              <SectionHeader title="Intelligence synthesis" subtitle="Company context and sharp opening hooks." />
              <p className="hero-copy">{synthesis.company_summary || "No synthesis summary available."}</p>
              <div className="tag-cloud">
                {(synthesis.buying_signals || []).map((item) => (
                  <StatusPill key={item} tone="good">
                    {item}
                  </StatusPill>
                ))}
                {(synthesis.pain_signals || []).map((item) => (
                  <StatusPill key={item} tone="risk">
                    {item}
                  </StatusPill>
                ))}
              </div>
            </Surface>

            <Surface>
              <SectionHeader title="Qualification snapshot" subtitle="The decision layer created from the report." />
              {meta?.qualification ? (
                <>
                  <div className="qualification-card">
                    <ScoreBadge label="Overall score" score={meta.qualification.overall_score || 0} />
                    <StatusPill tone={toneFromAction(meta.qualification.recommended_action)}>
                      {titleFromAction(meta.qualification.recommended_action)}
                    </StatusPill>
                  </div>
                  <p className="hero-copy">{meta.qualification.reasoning}</p>
                </>
              ) : (
                <p className="section-subtitle">Qualification data not returned.</p>
              )}
            </Surface>
          </div>

          <div className="report-grid">
            <CopyBlock label="Opening line" content={scripts.opening} />
            <CopyBlock label="Value proposition" content={scripts.value_proposition} />
            <CopyBlock label="Closing lines" content={scripts.closing_lines} />
            <CopyBlock label="Follow-up sequence" content={scripts.follow_up_sequence || []} />
          </div>
        </div>
      ) : null}
    </div>
  );
}
