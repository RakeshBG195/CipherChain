import { motion } from "framer-motion";
import { AlertTriangle, CheckCircle2, Loader2, ShieldAlert, ShieldCheck, XCircle } from "lucide-react";

export const Card = ({ className = "", children, ...p }) => (
  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className={`glass p-4 ${className}`} {...p}>{children}</motion.div>
);

export const PageTitle = ({ title, subtitle, icon: Icon }) => (
  <div className="mb-6">
    <h1 className="text-2xl md:text-3xl font-bold flex items-center gap-3">{Icon && <Icon className="text-neon-cyan" />}{title}</h1>
    {subtitle && <p className="text-slate-400 text-sm mt-1">{subtitle}</p>}
  </div>
);

export const Stat = ({ label, value, icon: Icon, tone = "cyan", hint }) => {
  const c = { cyan: "text-neon-cyan", purple: "text-neon-purple", blue: "text-neon-blue", red: "text-red-400", amber: "text-amber-400", green: "text-emerald-400" }[tone];
  return (
    <Card>
      <div className="flex items-center justify-between text-slate-400 text-xs uppercase tracking-wider">{label}{Icon && <Icon size={16} className={c} />}</div>
      <div className={`text-3xl font-bold mt-2 ${c}`}>{value}</div>
      {hint && <div className="text-xs text-slate-500 mt-1">{hint}</div>}
    </Card>
  );
};

const CAT = { SAFE: "text-emerald-300 bg-emerald-400/10 border-emerald-400/30", SPAM: "text-amber-300 bg-amber-400/10 border-amber-400/30", PHISHING: "text-red-300 bg-red-500/10 border-red-400/40" };
export const CategoryBadge = ({ category }) => <span className={`px-2 py-0.5 rounded-full border text-[11px] font-semibold ${CAT[category] || "text-slate-300 border-white/10"}`}>{category}</span>;

const CHAIN = {
  VERIFIED: ["text-emerald-300 bg-emerald-400/10 border-emerald-400/30", ShieldCheck],
  TAMPERED: ["text-red-300 bg-red-500/10 border-red-400/40", ShieldAlert],
  NOT_RECORDED: ["text-amber-300 bg-amber-400/10 border-amber-400/30", AlertTriangle],
  UNAVAILABLE: ["text-slate-300 bg-white/5 border-white/10", XCircle],
  PENDING: ["text-slate-300 bg-white/5 border-white/10", Loader2],
  RECORDED: ["text-cyan-200 bg-neon-cyan/10 border-neon-cyan/30", ShieldCheck],
  FAILED: ["text-red-300 bg-red-500/10 border-red-400/40", XCircle],
};
export const ChainBadge = ({ status }) => {
  const [cls, Icon] = CHAIN[status] || CHAIN.PENDING;
  return <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[11px] font-semibold ${cls}`}><Icon size={12} className={status === "PENDING" ? "animate-spin" : ""} />{status || "…"}</span>;
};

export const Banner = ({ tone = "amber", children }) => {
  const c = { amber: "border-amber-400/40 bg-amber-400/10 text-amber-200", red: "border-red-400/40 bg-red-500/10 text-red-200", cyan: "border-neon-cyan/30 bg-neon-cyan/5 text-cyan-100" }[tone];
  return <div className={`rounded-xl border px-4 py-3 text-sm mb-4 flex gap-2 ${c}`}><AlertTriangle size={18} className="shrink-0 mt-0.5" /><div>{children}</div></div>;
};

export const ErrorText = ({ error }) => (error ? <div className="text-sm text-red-300 flex items-center gap-2"><XCircle size={14} />{error}</div> : null);
export const Short = ({ s, n = 10 }) => <span className="font-mono">{s ? (s.length > n * 2 ? `${s.slice(0, n)}…${s.slice(-6)}` : s) : "—"}</span>;
export { CheckCircle2 };
