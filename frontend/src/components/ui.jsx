export function Surface({ children, className = "" }) {
  return <section className={`surface ${className}`.trim()}>{children}</section>;
}

export function MetricCard({ label, value, detail, tone = "default" }) {
  return (
    <Surface className={`metric-card tone-${tone}`}>
      <p className="metric-label">{label}</p>
      <strong className="metric-value">{value}</strong>
      {detail ? <span className="metric-detail">{detail}</span> : null}
    </Surface>
  );
}

export function SectionHeader({ eyebrow, title, subtitle, action }) {
  return (
    <div className="section-header">
      <div>
        {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
        <h3>{title}</h3>
        {subtitle ? <p className="section-subtitle">{subtitle}</p> : null}
      </div>
      {action}
    </div>
  );
}

export function ScoreBadge({ score, label }) {
  const tone = score >= 75 ? "good" : score >= 55 ? "warm" : score >= 35 ? "watch" : "risk";
  return (
    <div className={`score-badge tone-${tone}`}>
      <span>{label}</span>
      <strong>{score}</strong>
    </div>
  );
}

export function StatusPill({ children, tone = "default" }) {
  return <span className={`status-pill tone-${tone}`}>{children}</span>;
}

export function EmptyState({ title, body, action }) {
  return (
    <Surface className="empty-state">
      <div className="empty-orb" />
      <h3>{title}</h3>
      <p>{body}</p>
      {action}
    </Surface>
  );
}

export function LoadingState({ title = "Loading", body = "Pulling data from your workspace." }) {
  return (
    <Surface className="empty-state loading-state">
      <div className="pulse-stack">
        <span />
        <span />
        <span />
      </div>
      <h3>{title}</h3>
      <p>{body}</p>
    </Surface>
  );
}

export function CopyBlock({ label, content }) {
  const text = Array.isArray(content) ? content.join("\n\n") : content || "";

  async function handleCopy() {
    await navigator.clipboard.writeText(text);
  }

  return (
    <Surface className="copy-block">
      <div className="copy-head">
        <span>{label}</span>
        <button className="button button-ghost" onClick={handleCopy} type="button">
          Copy
        </button>
      </div>
      <pre>{text}</pre>
    </Surface>
  );
}

export function ProgressTimeline({ items }) {
  return (
    <div className="progress-timeline">
      {items.map((item, index) => (
        <div className="progress-item" key={`${item.message}-${index}`}>
          <div className="progress-marker">
            <span />
          </div>
          <div className="progress-body">
            <strong>{item.message}</strong>
            <small>
              Step {item.step} of {item.total}
            </small>
          </div>
        </div>
      ))}
    </div>
  );
}
