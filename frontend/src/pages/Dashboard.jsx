import { Activity, AlertOctagon, Brain, CheckCheck, Link2, Lock, MessageSquare, ShieldAlert } from "lucide-react";
import { Banner, Card, CategoryBadge, PageTitle, Stat } from "../components/ui";
import { CategoryPie, DailyBar } from "../components/Charts";
import { fmtDateTime } from "../lib/api";
import { useSummary } from "../lib/useSummary";

export default function Dashboard() {
  const { data, error } = useSummary();
  if (error) return <Banner tone="red">Could not load dashboard: {error}</Banner>;
  if (!data) return <div className="text-slate-400 animate-pulse">Loading real-time security data…</div>;
  const t = data.totals, m = data.model_metrics;
  return (
    <>
      <PageTitle title="Security Dashboard" subtitle="Live data from the API — nothing on this page is mocked." icon={Activity} />
      {m?.synthetic_data && <Banner>The loaded AI model was trained on <b>SYNTHETIC demo data</b>. Its metrics are not real-world performance. Retrain with real datasets (see README).</Banner>}
      {!m && <Banner tone="red">No trained model loaded. Run <code>python -m scripts.train_model</code>.</Banner>}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat label="Total messages" value={t.total_messages} icon={MessageSquare} />
        <Stat label="Encrypted (AES-256-GCM)" value={t.encrypted_messages} icon={Lock} tone="purple" />
        <Stat label="Blockchain verified" value={t.blockchain_verified} icon={Link2} tone="green" hint={`${t.blockchain_recorded} recorded on-chain`} />
        <Stat label="Tampered" value={t.tampered} icon={AlertOctagon} tone={t.tampered ? "red" : "cyan"} />
        <Stat label="Spam detected" value={t.spam_detected} icon={ShieldAlert} tone="amber" />
        <Stat label="Phishing detected" value={t.phishing_detected} icon={ShieldAlert} tone="red" />
        <Stat label="Messages scanned" value={t.scanned_messages} icon={CheckCheck} tone="blue" />
        <Stat label="AI model accuracy" value={m ? `${(m.accuracy * 100).toFixed(1)}%` : "—"} icon={Brain} tone="purple" hint={m ? (m.synthetic_data ? "synthetic data — not meaningful" : "held-out test set") : "no model"} />
      </div>
      <div className="grid lg:grid-cols-2 gap-4 mt-4">
        <Card><h3 className="font-semibold mb-2">Safe vs spam vs phishing</h3><CategoryPie dist={data.category_distribution} /></Card>
        <Card><h3 className="font-semibold mb-2">Daily message activity</h3><DailyBar data={data.daily_activity} /></Card>
      </div>
      <Card className="mt-4">
        <h3 className="font-semibold mb-3">Recent security events</h3>
        {!data.recent_events.length && <div className="text-sm text-slate-500">No events yet.</div>}
        <ul className="divide-y divide-white/5">
          {data.recent_events.map((e) => (
            <li key={e.id} className="py-2 flex flex-wrap items-center gap-2 text-sm">
              <span className="font-mono text-[11px] text-slate-400 w-40">{fmtDateTime(e.created_at)}</span>
              <span className={`text-xs px-2 py-0.5 rounded bg-white/5 ${e.type === "TAMPER_DETECTED" ? "text-red-300" : "text-slate-200"}`}>{e.type}</span>
              {e.category && <CategoryBadge category={e.category} />}
              {e.risk_score != null && <span className="text-xs text-slate-400">risk {e.risk_score}</span>}
              <span className="text-xs text-slate-500 truncate">{e.detail}</span>
            </li>
          ))}
        </ul>
      </Card>
    </>
  );
}
