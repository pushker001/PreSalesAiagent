import { Link } from "react-router-dom";

const proofPoints = [
  {
    title: "Research before the call",
    body: "Turn a lead's company footprint into sales-ready intelligence, buyer psychology, and opening hooks.",
  },
  {
    title: "Qualify with confidence",
    body: "Convert AI analysis into a clear score, recommended action, and next best move for every lead.",
  },
  {
    title: "Operate like a premium sales desk",
    body: "Move from one-off prep to a structured workspace for dashboard views, lead details, and saved report history.",
  },
];

const workflow = [
  "Lead intake and web enrichment",
  "Psychology and objection mapping",
  "Call strategy and scripts",
  "Qualification and recommended action",
];

export default function LandingPage() {
  return (
    <div className="landing-page">
      <header className="landing-topbar">
        <Link className="landing-brand" to="/">
          <span className="brand-mark">CA</span>
          <div>
            <p className="eyebrow">Coach OS</p>
            <strong>Closure Agent</strong>
          </div>
        </Link>

        <div className="landing-nav">
          <Link className="button button-ghost" to="/dashboard">
            View Workspace
          </Link>
          <Link className="button button-primary" to="/analyze">
            Try Lead Analysis
          </Link>
        </div>
      </header>

      <main className="landing-main">
        <section className="landing-hero">
          <div className="landing-copy">
            <p className="eyebrow">AI sales intelligence for coaches</p>
            <h1>Walk into every call knowing the psychology, objections, and next best action.</h1>
            <p className="landing-lead">
              Closure Agent helps business coaches research leads, prepare sharper calls, score
              opportunities, and operate from a premium sales workspace instead of scattered notes
              and guesswork.
            </p>

            <div className="landing-actions">
              <Link className="button button-primary" to="/analyze">
                Analyze your next lead
              </Link>
              <Link className="button button-ghost" to="/dashboard">
                Explore dashboard
              </Link>
            </div>

            <div className="landing-proof-bar">
              <span>Research</span>
              <span>Qualification</span>
              <span>Scripts</span>
              <span>Reports</span>
            </div>
          </div>

          <div className="landing-showcase surface">
            <div className="showcase-header">
              <div>
                <p className="eyebrow">What coaches see</p>
                <h2>One system for pre-call clarity and pipeline action.</h2>
              </div>
              <span className="status-pill tone-good">Live workflow</span>
            </div>

            <div className="showcase-grid">
              <div className="showcase-card tone-good">
                <p className="metric-label">Qualification</p>
                <strong className="showcase-value">78</strong>
                <span className="status-pill tone-good">Book Call</span>
              </div>
              <div className="showcase-card tone-watch">
                <p className="metric-label">Intelligence score</p>
                <strong className="showcase-value">84</strong>
                <p>Strong buying signals and clear personalization hooks.</p>
              </div>
            </div>

            <div className="showcase-list">
              {workflow.map((item) => (
                <div className="showcase-item" key={item}>
                  <span className="signal-dot" />
                  <p>{item}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="landing-section">
          <div className="section-heading">
            <p className="eyebrow">Why it matters</p>
            <h2>Built for coaches who sell high-trust offers, not just pipeline volume.</h2>
          </div>

          <div className="landing-feature-grid">
            {proofPoints.map((item) => (
              <article className="surface landing-feature-card" key={item.title}>
                <h3>{item.title}</h3>
                <p>{item.body}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="landing-section landing-band">
          <div className="section-heading">
            <p className="eyebrow">System flow</p>
            <h2>From raw lead input to a sales-ready operating view.</h2>
          </div>

          <div className="landing-flow">
            <div className="landing-flow-step">
              <span>01</span>
              <strong>Analyze lead</strong>
              <p>Collect company inputs and run the AI workflow across research, psychology, and scripts.</p>
            </div>
            <div className="landing-flow-step">
              <span>02</span>
              <strong>Save the outcome</strong>
              <p>Store lead records, report history, and qualification results in a structured workspace.</p>
            </div>
            <div className="landing-flow-step">
              <span>03</span>
              <strong>Act with confidence</strong>
              <p>Open the dashboard, inspect the lead detail page, and move directly into the right next action.</p>
            </div>
          </div>
        </section>

        <section className="surface landing-cta">
          <div>
            <p className="eyebrow">Start here</p>
            <h2>Give your coaching business a sharper sales front end.</h2>
            <p>
              Launch a lead analysis now, then review the dashboard and lead workspace to see how
              the system supports real selling decisions.
            </p>
          </div>
          <div className="landing-actions">
            <Link className="button button-primary" to="/analyze">
              Run first analysis
            </Link>
            <Link className="button button-ghost" to="/dashboard">
              Open workspace
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
}
