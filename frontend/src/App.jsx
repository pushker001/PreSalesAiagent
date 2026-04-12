import { useState } from "react";

// ─── Helpers ─────────────────────────────────────────────────────────────────
function scoreColor(s) {
  if (s >= 70) return "#22c55e";
  if (s >= 45) return "#eab308";
  if (s >= 20) return "#f97316";
  return "#ef4444";
}
function scoreLabel(s) {
  if (s >= 70) return "High";
  if (s >= 45) return "Medium";
  if (s >= 20) return "Low";
  return "Minimal";
}
function urgencyColor(u) {
  return u === "high" ? "#ef4444" : u === "medium" ? "#eab308" : "#22c55e";
}

// ─── Components ──────────────────────────────────────────────────────────────
function Section({ title, children }) {
  const [open, setOpen] = useState(true);
  return (
    <div style={{ marginBottom: 12, background: "#1e293b", borderRadius: 12, overflow: "hidden" }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          width: "100%", textAlign: "left", padding: "14px 20px",
          background: "none", border: "none", cursor: "pointer",
          color: "#e2e8f0", fontWeight: 600, fontSize: 15,
          display: "flex", justifyContent: "space-between",
        }}
      >
        {title}
        <span style={{ color: "#475569" }}>{open ? "▲" : "▼"}</span>
      </button>
      {open && <div style={{ padding: "0 20px 20px" }}>{children}</div>}
    </div>
  );
}

function Tag({ text, color = "#6366f1" }) {
  return (
    <span style={{
      display: "inline-block", background: `${color}22`,
      color, border: `1px solid ${color}44`,
      borderRadius: 6, padding: "2px 10px", fontSize: 12, margin: "3px 3px 3px 0",
    }}>
      {text}
    </span>
  );
}

function CopyBox({ label, content }) {
  const [copied, setCopied] = useState(false);
  const text = Array.isArray(content) ? content.join("\n\n") : (content || "");
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
        <span style={{ color: "#94a3b8", fontSize: 12, fontWeight: 600 }}>{label}</span>
        <button
          onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1500); }}
          style={{
            background: copied ? "#22c55e22" : "#334155", border: "none",
            color: copied ? "#22c55e" : "#94a3b8", borderRadius: 6,
            padding: "4px 12px", fontSize: 11, cursor: "pointer",
          }}
        >
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
      <pre style={{
        background: "#0f172a", color: "#e2e8f0", padding: 14,
        borderRadius: 8, fontSize: 12, whiteSpace: "pre-wrap", margin: 0,
      }}>{text}</pre>
    </div>
  );
}

function IntelScoreBadge({ score }) {
  const color = scoreColor(score);
  const label = scoreLabel(score);
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 16,
      background: "#1e293b", borderRadius: 12, padding: "16px 24px",
      border: `2px solid ${color}`, marginBottom: 20,
    }}>
      <svg width={72} height={72} viewBox="0 0 72 72">
        <circle cx={36} cy={36} r={30} fill="none" stroke="#334155" strokeWidth={7} />
        <circle
          cx={36} cy={36} r={30} fill="none" stroke={color} strokeWidth={7}
          strokeDasharray={`${(score / 100) * 188.5} 188.5`}
          strokeLinecap="round" transform="rotate(-90 36 36)"
        />
        <text x={36} y={41} textAnchor="middle" fill={color} fontSize={16} fontWeight="700">{score}</text>
      </svg>
      <div>
        <div style={{ fontSize: 11, color: "#94a3b8", textTransform: "uppercase", letterSpacing: 1 }}>
          Intelligence Score
        </div>
        <div style={{ fontSize: 22, fontWeight: 700, color }}>{label}</div>
        <div style={{ fontSize: 12, color: "#94a3b8", marginTop: 4 }}>
          Data completeness · Signal richness · Urgency
        </div>
      </div>
    </div>
  );
}

const SELECT_CLS = {
  width: "100%", background: "#1e293b", border: "1px solid #334155",
  borderRadius: 8, color: "#e2e8f0", padding: "10px 14px", fontSize: 14,
};
const INPUT_CLS = { ...SELECT_CLS };

// ─── App ─────────────────────────────────────────────────────────────────────
export default function App() {
  const [form, setForm] = useState({
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
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [progress, setProgress] = useState([]);


  const handleChange = e => setForm(f => ({ ...f, [e.target.name]: e.target.value }));

  const handleSubmit = async () => {
    setLoading(true); setError(""); setResult(null); setProgress([]);
    try {
      const res = await fetch("http://localhost:8000/analyze-closure", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Server error ${res.status}: ${text}`);
      }
  
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
  
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
  
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); // keep incomplete last line in buffer
  
        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;
          try {
            const event = JSON.parse(trimmed);
            if (event.event === "progress") {
              setProgress(p => [...p, { message: event.message, step: event.step, total: event.total }]);
            } else if (event.event === "done") {
              setResult(event.data.closure_report);
            } else if (event.event === "error") {
              throw new Error(event.message);
            }
          } catch (parseErr) {
            console.warn("Failed to parse line:", trimmed);
          }
        }
      }
    } catch (e) {
      setError(e.message || "Stream disconnected unexpectedly");
    } finally {
      setLoading(false);
    }
  };
  
  const s = result?.synthesis || {};
  const score = result?.intelligence_score ?? 0;

  return (
    <div style={{
      minHeight: "100vh", background: "#0f172a", color: "#e2e8f0",
      fontFamily: "Inter, system-ui, sans-serif", padding: "40px 20px",
    }}>
      <div style={{ maxWidth: 900, margin: "0 auto" }}>

        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: 36 }}>
          <h1 style={{ fontSize: 28, fontWeight: 800, margin: 0, color: "#f8fafc" }}>
            🧠 Coach Call Intelligence System
          </h1>
          <p style={{ color: "#64748b", marginTop: 8 }}>
            6-layer intelligence · LLM synthesis · Personalized scripts
          </p>
        </div>

        {/* ── FORM ─────────────────────────────────────────────────────── */}
        <div style={{ background: "#1e293b", borderRadius: 16, padding: 32, marginBottom: 28 }}>
          <h2 style={{ marginTop: 0, marginBottom: 24, fontSize: 17 }}>Prospect Details</h2>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 24px" }}>

            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", color: "#94a3b8", fontSize: 12, marginBottom: 6 }}>Client Name *</label>
              <input name="client_name" value={form.client_name} onChange={handleChange} placeholder="Freshworks" style={INPUT_CLS} />
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", color: "#94a3b8", fontSize: 12, marginBottom: 6 }}>Website URL</label>
              <input name="website_url" value={form.website_url} onChange={handleChange} placeholder="https://freshworks.com" style={INPUT_CLS} />
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", color: "#94a3b8", fontSize: 12, marginBottom: 6 }}>Client Type</label>
              <select name="client_type" value={form.client_type} onChange={handleChange} style={SELECT_CLS}>
                <option>Solo Founder</option>
                <option>Agency Owner</option>
                <option>Startup Founder</option>
                <option>Enterprise Executive</option>
                <option>Organization / Association</option>
              </select>
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", color: "#94a3b8", fontSize: 12, marginBottom: 6 }}>Revenue Stage</label>
              <select name="revenue_stage" value={form.revenue_stage} onChange={handleChange} style={SELECT_CLS}>
                <option>Idea Stage</option>
                <option>Early Stage (&lt;$1M)</option>
                <option>Scaling ($1M-$5M)</option>
                <option>Established ($5M+)</option>
              </select>
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", color: "#94a3b8", fontSize: 12, marginBottom: 6 }}>Lead Source</label>
              <select name="lead_source" value={form.lead_source} onChange={handleChange} style={SELECT_CLS}>
                <option>Inbound</option>
                <option>Outbound</option>
                <option>Referral</option>
                <option>Event / Conference</option>
              </select>
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", color: "#94a3b8", fontSize: 12, marginBottom: 6 }}>Lead Temperature</label>
              <select name="lead_temperature" value={form.lead_temperature} onChange={handleChange} style={SELECT_CLS}>
                <option>Cold</option>
                <option>Warm</option>
                <option>Hot</option>
              </select>
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", color: "#94a3b8", fontSize: 12, marginBottom: 6 }}>Coach Offer Price Range</label>
              <select name="coach_offer_price_range" value={form.coach_offer_price_range} onChange={handleChange} style={SELECT_CLS}>
                <option>$3k-$10k</option>
                <option>$10k-$25k</option>
                <option>$25k-$50k</option>
                <option>$50k+</option>
              </select>
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", color: "#94a3b8", fontSize: 12, marginBottom: 6 }}>Offer Type</label>
              <select name="offer_type" value={form.offer_type} onChange={handleChange} style={SELECT_CLS}>
                <option>Strategic Consulting</option>
                <option>High-Ticket Coaching</option>
                <option>Enterprise Consulting</option>
              </select>
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", color: "#94a3b8", fontSize: 12, marginBottom: 6 }}>Call Goal</label>
              <select name="call_goal" value={form.call_goal} onChange={handleChange} style={SELECT_CLS}>
                <option>Discovery Call</option>
                <option>Sales Call</option>
                <option>Strategic Partnership / Consulting Qualification</option>
              </select>
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", color: "#94a3b8", fontSize: 12, marginBottom: 6 }}>LinkedIn URL (optional)</label>
              <input name="linkedin_url" value={form.linkedin_url} onChange={handleChange} placeholder="https://linkedin.com/in/..." style={INPUT_CLS} />
            </div>

          </div>

          {/* Full width fields */}
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", color: "#94a3b8", fontSize: 12, marginBottom: 6 }}>Problem Mentioned</label>
            <textarea name="problem_mentioned" value={form.problem_mentioned} onChange={handleChange}
              placeholder="What problem did the client mention?" rows={2}
              style={{ ...INPUT_CLS, resize: "vertical" }} />
          </div>

          <div style={{ marginBottom: 24 }}>
            <label style={{ display: "block", color: "#94a3b8", fontSize: 12, marginBottom: 6 }}>
              LinkedIn Summary <span style={{ color: "#475569" }}>(paste from profile — boosts intelligence score)</span>
            </label>
            <textarea name="linkedin_summary" value={form.linkedin_summary} onChange={handleChange}
              placeholder="Paste raw text from their LinkedIn About section or company page..." rows={4}
              style={{ ...INPUT_CLS, resize: "vertical" }} />
          </div>

          <button
            onClick={handleSubmit} disabled={loading}
            style={{
              width: "100%", padding: "14px 0",
              background: loading ? "#334155" : "#6366f1",
              color: "#fff", border: "none", borderRadius: 10,
              fontSize: 16, fontWeight: 700, cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "⚡ Running..." : "⚡ Prepare My Call"}
          </button>

          {progress.length > 0 && (
            <div style={{ marginTop: 16, background: "#0f172a", borderRadius: 8, padding: 16 }}>
              {progress.map((p, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                  <div style={{ width: 120, height: 4, background: "#1e293b", borderRadius: 4, flexShrink: 0 }}>
                    <div style={{
                      width: `${(p.step / p.total) * 100}%`,
                      height: "100%", background: "#6366f1", borderRadius: 4,
                      transition: "width 0.3s ease"
                    }} />
                  </div>
                  <span style={{ color: "#94a3b8", fontSize: 13 }}>{p.message}</span>
                </div>
              ))}
            </div>
          )}

          {error && (
            <div style={{ marginTop: 16, background: "#7f1d1d", color: "#fca5a5", borderRadius: 8, padding: 12, fontSize: 13 }}>
              {error}
            </div>
          )}
        </div>

        {/* ── RESULTS ──────────────────────────────────────────────────── */}
        {result && (
          <div>
            {/* Intelligence Score */}
            <IntelScoreBadge score={score} />

            {/* Synthesis */}
            <Section title="🧠 Intelligence Synthesis">
              {s.company_summary && (
                <p style={{ color: "#94a3b8", marginBottom: 16 }}>{s.company_summary}</p>
              )}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
                {[
                  ["⚡ Pain Signals",          s.pain_signals,          "#ef4444"],
                  ["✅ Buying Signals",         s.buying_signals,        "#22c55e"],
                  ["🎯 Personalization Hooks",  s.personalization_hooks, "#818cf8"],
                  ["⚠️ Risk Flags",             s.risk_flags,            "#f97316"],
                ].map(([label, items, color]) => (
                  <div key={label} style={{ background: "#0f172a", borderRadius: 8, padding: 14, borderLeft: `4px solid ${color}` }}>
                    <div style={{ color, fontSize: 12, fontWeight: 600, marginBottom: 8 }}>{label}</div>
                    {(items || []).length === 0
                      ? <div style={{ color: "#475569", fontSize: 12 }}>None detected</div>
                      : (items || []).map((item, i) => (
                          <div key={i} style={{ color: "#cbd5e1", fontSize: 13, marginBottom: 4 }}>• {item}</div>
                        ))
                    }
                  </div>
                ))}
              </div>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <Tag text={`Stage: ${s.growth_stage || "unknown"}`} color="#6366f1" />
                <Tag text={`Urgency: ${s.urgency_level || "medium"}`} color={urgencyColor(s.urgency_level)} />
                {s.recommended_angle && <Tag text={s.recommended_angle} color="#0ea5e9" />}
              </div>
            </Section>

            {/* Client Mindset */}
            <Section title="🔍 Client Mindset">
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                {[
                  ["Pain Points",        result.psychology?.pain_points,    "#ef4444"],
                  ["Motivations",        result.psychology?.motivations,    "#22c55e"],
                  ["Fears",              result.psychology?.fears,          "#f97316"],
                ].map(([label, items, color]) => (
                  <div key={label} style={{ background: "#0f172a", borderRadius: 8, padding: 12 }}>
                    <div style={{ color, fontSize: 12, fontWeight: 600, marginBottom: 6 }}>{label}</div>
                    {(items || []).map((t, i) => (
                      <div key={i} style={{ color: "#cbd5e1", fontSize: 12, marginBottom: 3 }}>• {t}</div>
                    ))}
                  </div>
                ))}
                <div style={{ background: "#0f172a", borderRadius: 8, padding: 12 }}>
                  <div style={{ color: "#818cf8", fontSize: 12, fontWeight: 600, marginBottom: 6 }}>Profile</div>
                  <div style={{ color: "#cbd5e1", fontSize: 12, marginBottom: 3 }}>
                    <b>Decision Style:</b> {result.psychology?.decision_making_style}
                  </div>
                  <div style={{ color: "#cbd5e1", fontSize: 12, marginBottom: 3 }}>
                    <b>Trust Level:</b> {result.psychology?.trust_level}
                  </div>
                  <div style={{ color: "#cbd5e1", fontSize: 12 }}>
                    <b>Urgency:</b> {result.psychology?.urgency_level}
                  </div>
                </div>
              </div>
            </Section>

            {/* Objections */}
            <Section title="⚠️ Likely Resistance">
              {(result.objections || []).map((o, i) => (
                <div key={i} style={{
                  background: "#0f172a", borderRadius: 8, padding: 14, marginBottom: 10,
                  borderLeft: `3px solid #6366f1`,
                }}>
                  <div style={{ color: "#f1f5f9", fontWeight: 600, marginBottom: 4 }}>"{o.objection}"</div>
                  <Tag text={`${o.probability} probability`} color={o.probability === "high" ? "#ef4444" : o.probability === "medium" ? "#eab308" : "#22c55e"} />
                  <div style={{ color: "#94a3b8", fontSize: 13, marginTop: 8, marginBottom: 4 }}>
                    <b style={{ color: "#e2e8f0" }}>Response:</b> {o.response_strategy}
                  </div>
                  <div style={{ color: "#6366f1", fontSize: 12 }}>
                    <b>Reframe:</b> {o.reframe_technique}
                  </div>
                </div>
              ))}
            </Section>

            {/* Strategy */}
            <Section title="🎯 Closing Strategy">
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                {[
                  ["Recommended Close Type", result.strategy?.recommended_close_type, "#6366f1"],
                  ["Positioning Angle",      result.strategy?.positioning,            "#0ea5e9"],
                  ["Urgency Angle",          result.strategy?.urgency_angle,          "#ef4444"],
                  ["Authority Lever",        result.strategy?.authority_lever,        "#22c55e"],
                  ["Timing",                 result.strategy?.timing_recommendation,  "#eab308"],
                  ["Risk Mitigation",        result.strategy?.risk_mitigation,        "#f97316"],
                ].map(([label, val, color]) => val ? (
                  <div key={label} style={{ background: "#0f172a", borderRadius: 8, padding: 12 }}>
                    <div style={{ color, fontSize: 11, fontWeight: 600, marginBottom: 4 }}>{label}</div>
                    <div style={{ color: "#cbd5e1", fontSize: 13 }}>{val}</div>
                  </div>
                ) : null)}
              </div>
            </Section>

            {/* Call Playbook */}
            <Section title="🗣 Call Playbook">
              <CopyBox label="🎙 OPENING LINE" content={result.scripts?.opening} />

              <div style={{ marginBottom: 16 }}>
                <div style={{ color: "#94a3b8", fontSize: 12, fontWeight: 600, marginBottom: 8 }}>🔍 DISCOVERY QUESTIONS</div>
                <ol style={{ paddingLeft: 20, margin: 0 }}>
                  {(result.scripts?.discovery_questions || []).map((q, i) => (
                    <li key={i} style={{ color: "#cbd5e1", fontSize: 13, marginBottom: 6 }}>{q}</li>
                  ))}
                </ol>
              </div>

              <CopyBox label="💡 VALUE PROPOSITION" content={result.scripts?.value_proposition} />
              <CopyBox label="🎯 CLOSING LINES"     content={result.scripts?.closing_lines} />

              <div style={{ marginBottom: 16 }}>
                <div style={{ color: "#94a3b8", fontSize: 12, fontWeight: 600, marginBottom: 8 }}>📩 FOLLOW-UP SEQUENCE</div>
                {(result.scripts?.follow_up_sequence || []).map((msg, i) => (
                  <div key={i} style={{
                    background: "#0f172a", borderRadius: 8, padding: 12, marginBottom: 8,
                    borderLeft: "3px solid #6366f1",
                  }}>
                    <div style={{ color: "#6366f1", fontSize: 11, fontWeight: 600, marginBottom: 4 }}>
                      {i === 0 ? "Day 1" : i === 1 ? "Day 3" : "Day 7"}
                    </div>
                    <div style={{ color: "#cbd5e1", fontSize: 13 }}>{msg}</div>
                  </div>
                ))}
              </div>
            </Section>

          </div>
        )}
      </div>
    </div>
  );
}
