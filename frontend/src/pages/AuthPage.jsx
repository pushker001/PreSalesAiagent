import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { login, signup } from "../lib/api";
import { useAuth } from "../lib/auth";

export default function AuthPage() {
  const { saveToken } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const redirectTo = location.state?.from?.pathname || "/dashboard";

  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ email: "", password: "", org_name: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleChange(e) {
    setForm((current) => ({ ...current, [e.target.name]: e.target.value }));
    setError("");
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const result =
        mode === "login"
          ? await login(form.email, form.password)
          : await signup(form.email, form.password, form.org_name);

      saveToken(result.access_token);
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <p className="eyebrow">AI Closure Agent</p>
        <h1>{mode === "login" ? "Welcome back" : "Create your account"}</h1>
        <p className="section-subtitle">
          {mode === "login" ? "Sign in to your coaching workspace." : "Set up your coaching workspace."}
        </p>

        <form className="lead-state-form" onSubmit={handleSubmit}>
          <label className="field">
            <span>Email</span>
            <input name="email" onChange={handleChange} placeholder="you@example.com" type="email" value={form.email} required />
          </label>

          <label className="field">
            <span>Password</span>
            <input name="password" onChange={handleChange} placeholder="••••••••" type="password" value={form.password} required />
          </label>

          {mode === "signup" ? (
            <label className="field">
              <span>Organization name</span>
              <input name="org_name" onChange={handleChange} placeholder="My Coaching Business" value={form.org_name} required />
            </label>
          ) : null}

          {error ? <div className="inline-error">{error}</div> : null}

          <button className="button button-primary" disabled={loading} type="submit">
            {loading ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
          </button>
        </form>

        <p className="section-subtitle" style={{ marginTop: "1rem", textAlign: "center" }}>
          {mode === "login" ? "Don't have an account?" : "Already have an account?"}{" "}
          <button
            className="button button-ghost"
            onClick={() => { setMode(mode === "login" ? "signup" : "login"); setError(""); }}
            type="button"
          >
            {mode === "login" ? "Sign up" : "Sign in"}
          </button>
        </p>
      </div>
    </div>
  );
}
