import { useEffect, useState } from "react";
import { Brain, ScanSearch } from "lucide-react";
import { Banner, Card, CategoryBadge, ErrorText, PageTitle } from "../components/ui";
import { api, fmtDateTime } from "../lib/api";

const SAMPLES = [
  "Hey, are we still meeting for lunch at noon tomorrow?",
  "WINNER! You have won a free iPhone. Text CLAIM to 85555 now to get your prize",
  "Security alert: your PayPal account is suspended. Verify your password at http://secure-login.xyz/verify immediately",
];

export default function Threats() {
  const [text, setText] = useState(""); const [res, setRes] = useState(null);
  const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState(null); const [threats, setThreats] = useState([]);
  const refresh = () => api("/ai/threats").then(setThreats).catch(() => {});
  useEffect(() => { api("/ai/status").then(setStatus).catch((e) => setErr(e.message)); refresh(); }, []);

  const scan = async () => {
    setBusy(true); setErr("");
    try { setRes(await api("/ai/analyze", { method: "POST", body: { text } })); refresh(); } catch (e) { setErr(e.message); } finally { setBusy(false); }
  };
  const tone = res?.category === "PHISHING" ? "text-red-400" : res?.category === "SPAM" ? "text-amber-400" : "text-emerald-400";
  return (
    <>
      <PageTitle title="AI Threat Detection" subtitle="TF-IDF + Logistic Regression model loaded from disk. Text you scan here is analysed in memory and not stored." icon={Brain} />
      {status && !status.loaded && <Banner tone="red">{status.error}</Banner>}
      {status?.synthetic_data && <Banner>Model trained on SYNTHETIC demo data — predictions on real messages may be unreliable until retrained on real datasets.</Banner>}
      <div className="grid lg:grid-cols-2 gap-4">
        <Card>
          <label className="label">Message to analyse</label>
          <textarea className="input h-36" value={text} onChange={(e) => setText(e.target.value)} placeholder="Paste a message…" />
          <div className="flex flex-wrap gap-2 mt-3">{SAMPLES.map((s, i) => <button key={i} className="btn-ghost text-xs" onClick={() => setText(s)}>Sample {i + 1}</button>)}</div>
          <button className="btn-primary mt-4" disabled={busy || !text.trim()} onClick={scan}><ScanSearch size={16} />{busy ? "Analysing…" : "Analyse"}</button>
          <div className="mt-3"><ErrorText error={err} /></div>
        </Card>
        <Card>
          {!res ? <div className="text-slate-500 text-sm">Result will appear here.</div> : (
            <div className="space-y-3">
              <div className="flex items-center justify-between"><div className={`text-3xl font-bold ${tone}`}>{res.category}</div><CategoryBadge category={res.category} /></div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="glass p-3"><div className="text-xs text-slate-400">Risk score</div><div className="text-2xl font-bold">{res.risk_score}<span className="text-sm text-slate-400">/100</span></div></div>
                <div className="glass p-3"><div className="text-xs text-slate-400">Confidence</div><div className="text-2xl font-bold">{(res.confidence * 100).toFixed(1)}%</div></div>
              </div>
              <div className="space-y-1">{Object.entries(res.probabilities).map(([k, v]) => (
                <div key={k} className="text-xs"><div className="flex justify-between"><span>{k}</span><span>{(v * 100).toFixed(1)}%</span></div>
                  <div className="h-1.5 rounded bg-white/10"><div className="h-full rounded bg-gradient-to-r from-neon-cyan to-neon-purple" style={{ width: `${v * 100}%` }} /></div></div>))}</div>
              <p className="text-sm text-slate-300">{res.explanation}</p>
              {res.top_terms.length > 0 && <div className="flex flex-wrap gap-1">{res.top_terms.map((t) => <span key={t.term} className="text-[11px] font-mono px-2 py-0.5 rounded bg-neon-purple/15 text-purple-200">{t.term} +{t.weight}</span>)}</div>}
              {res.indicators.length > 0 && <div><div className="text-xs text-slate-400 mb-1">Surface indicators (informational, not model inputs)</div><ul className="text-xs list-disc pl-4 text-slate-300">{res.indicators.map((i) => <li key={i}>{i}</li>)}</ul></div>}
            </div>)}
        </Card>
      </div>
      <Card className="mt-4">
        <h3 className="font-semibold mb-3">Recent detections</h3>
        {!threats.length && <div className="text-sm text-slate-500">Nothing scanned yet.</div>}
        <ul className="divide-y divide-white/5 text-sm">{threats.map((t) => (
          <li key={t.id} className="py-2 flex flex-wrap gap-3 items-center"><span className="font-mono text-[11px] text-slate-400 w-40">{fmtDateTime(t.created_at)}</span><CategoryBadge category={t.category} /><span className="text-xs text-slate-400">risk {t.risk_score}</span><span className="text-xs text-slate-500">{t.type === "MANUAL_SCAN" ? "manual scan" : `message #${t.message_id}`}</span></li>))}</ul>
      </Card>
    </>
  );
}
