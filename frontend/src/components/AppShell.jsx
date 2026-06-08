import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";

const navigation = [
  { to: "/dashboard", label: "Dashboard", hint: "Lead priorities" },
  { to: "/analyze", label: "Analyze Lead", hint: "Run AI workflow" },
  { to: "/settings", label: "Settings", hint: "Rules & Brand Voice" },
];

export default function AppShell() {
  const { clearToken } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    clearToken();
    navigate("/auth");
  }

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="brand-mark">CA</div>
        <div className="brand-copy">
          <p className="eyebrow">Coach OS</p>
          <h1>Closure Agent</h1>
          <p>AI sales intelligence for serious coaching businesses.</p>
        </div>

        <nav className="sidebar-nav">
          {navigation.map((item) => (
            <NavLink
              key={item.to}
              className={({ isActive }) => `nav-link${isActive ? " is-active" : ""}`}
              to={item.to}
            >
              <span>{item.label}</span>
              <small>{item.hint}</small>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <p className="eyebrow">Why it wins</p>
          <p>
            Prepare faster, qualify better, and move leads into the right next action with
            confidence.
          </p>
          <button className="button button-ghost" onClick={handleLogout} type="button" style={{ marginTop: "1rem", width: "100%" }}>
            Sign out
          </button>
        </div>
      </aside>

      <div className="app-main-wrap">
        <header className="topbar">
          <div>
            <p className="eyebrow">Premium sales workspace</p>
            <h2>Lead intelligence, qualification, and action in one place</h2>
          </div>
          <NavLink className="button button-primary" to="/analyze">
            Analyze New Lead
          </NavLink>
        </header>

        <main className="app-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
