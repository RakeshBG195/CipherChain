import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ErrorText } from "../components/ui";
import AuthShell from "./AuthShell";

export default function Login() {
  const { user, login } = useAuth();
  const nav = useNavigate();
  const [f, setF] = useState({ username: "", password: "" });
  const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);
  if (user) return <Navigate to="/" replace />;
  const submit = async (e) => {
    e.preventDefault(); setBusy(true); setErr("");
    try { await login(f.username, f.password); nav("/"); } catch (x) { setErr(x.message); } finally { setBusy(false); }
  };
  return (
    <AuthShell title="Welcome back" subtitle="Sign in to your encrypted workspace">
      <form onSubmit={submit} className="space-y-4">
        <div><label className="label">Username or email</label><input className="input" autoFocus value={f.username} onChange={(e) => setF({ ...f, username: e.target.value })} required /></div>
        <div><label className="label">Password</label><input className="input" type="password" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} required /></div>
        <ErrorText error={err} />
        <button className="btn-primary w-full" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
      </form>
      <p className="text-sm text-slate-400 mt-6">No account? <Link className="text-neon-cyan" to="/register">Register</Link></p>
    </AuthShell>
  );
}
