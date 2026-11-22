import { BarChart3 } from "lucide-react";
import { Banner, Card, PageTitle } from "../components/ui";
import { CategoryPie, ConfusionMatrix, DailyBar, MetricsBar, ThreatLine } from "../components/Charts";
import { useSummary } from "../lib/useSummary";

export default function Analytics() {
  const { data, error } = useSummary(15000);
  if (error) return <Banner tone="red">{error}</Banner>;
  if (!data) return <div className="text-slate-400 animate-pulse">Loading…</div>;
  const m = data.model_metrics;
  return (
    <>
      <PageTitle title="Analytics" subtitle="Message activity, threat history and the trained model's evaluation." icon={BarChart3} />
      {m?.synthetic_data && <Banner>{m.warning}</Banner>}
      <div className="grid lg:grid-cols-2 gap-4">
        <Card><h3 className="font-semibold mb-2">Category distribution</h3><CategoryPie dist={data.category_distribution} /></Card>
        <Card><h3 className="font-semibold mb-2">Daily message activity (14 days)</h3><DailyBar data={data.daily_activity} /></Card>
        <Card><h3 className="font-semibold mb-2">Threat detection history</h3><ThreatLine data={data.threat_history} /></Card>
        <Card><h3 className="font-semibold mb-2">ML evaluation (macro averages)</h3><MetricsBar metrics={m} /></Card>
      </div>
      {m && (
        <div className="grid lg:grid-cols-2 gap-4 mt-4">
          <Card><h3 className="font-semibold mb-3">Confusion matrix (held-out test set, n={m.n_test})</h3><ConfusionMatrix cm={m.confusion_matrix} /></Card>
          <Card>
            <h3 className="font-semibold mb-3">Per-class metrics</h3>
            <table className="w-full text-sm"><thead className="text-xs text-slate-400"><tr><th className="text-left p-1">Class</th><th>Precision</th><th>Recall</th><th>F1</th><th>Support</th></tr></thead>
              <tbody>{Object.entries(m.per_class).map(([k, v]) => (
                <tr key={k} className="text-center border-t border-white/5"><td className="text-left p-1">{k}</td><td>{v.precision.toFixed(3)}</td><td>{v.recall.toFixed(3)}</td><td>{v.f1.toFixed(3)}</td><td>{v.support}</td></tr>))}</tbody></table>
            <p className="text-xs text-slate-500 mt-3">Dataset: {m.dataset} · train {m.n_train} / test {m.n_test} · trained {new Date(m.trained_at).toLocaleString()}</p>
            <ul className="text-xs text-slate-500 mt-2 list-disc pl-4">{m.limitations.map((l) => <li key={l}>{l}</li>)}</ul>
          </Card>
        </div>
      )}
    </>
  );
}
