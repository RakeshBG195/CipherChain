import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ErrorText } from "../components/ui";
import AuthShell from "./AuthShell";

export default function Register() {
  const { user, register } = useAuth();
  const nav = useNavigate();
  const [f, setF] = useState({ display_name: "", username: "", email: "", password: "" });
  const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);
  if (user) return <Navigate to="/" replace />;
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const submit = async (e) => {
    e.preventDefault(); setBusy(true); setErr("");
    try { await register(f); nav("/"); } catch (x) { setErr(x.message); } finally { setBusy(false); }
  };
  return (
    <AuthShell title="Create account" subtitle="An encryption key pair is generated in your browser. The private key never leaves this device.">
      <form onSubmit={submit} className="space-y-3">
        <div><label className="label">Display name</label><input className="input" value={f.display_name} onChange={set("display_name")} required /></div>
        <div><label className="label">Username (letters, digits, _)</label><input className="input" value={f.username} onChange={set("username")} pattern="[A-Za-z0-9_]{3,32}" required /></div>
        <div><label className="label">Email</label><input className="input" type="email" value={f.email} onChange={set("email")} required /></div>
        <div><label className="label">Password (min 8 characters)</label><input className="input" type="password" minLength={8} value={f.password} onChange={set("password")} required /></div>
        <ErrorText error={err} />
        <button className="btn-primary w-full" disabled={busy}>{busy ? "Generating keys…" : "Register"}</button>
      </form>
      <p className="text-sm text-slate-400 mt-6">Already registered? <Link className="text-neon-cyan" to="/login">Sign in</Link></p>
    </AuthShell>
  );
}
