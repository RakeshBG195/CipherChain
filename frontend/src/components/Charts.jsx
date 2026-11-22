import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export const COLORS = { SAFE: "#34d399", SPAM: "#fbbf24", PHISHING: "#f43f5e" };
const tip = { contentStyle: { background: "#0b1226", border: "1px solid rgba(255,255,255,.12)", borderRadius: 12, fontSize: 12 } };
const axis = { stroke: "#64748b", fontSize: 11 };
const short = (d) => d.slice(5);

export function CategoryPie({ dist }) {
  const data = Object.entries(dist || {}).map(([name, value]) => ({ name, value }));
  if (!data.some((d) => d.value > 0)) return <Empty text="No scanned messages yet" />;
  return (
    <ResponsiveContainer width="100%" height={240}><PieChart>
      <Pie data={data} dataKey="value" nameKey="name" innerRadius={55} outerRadius={85} paddingAngle={3}>{data.map((d) => <Cell key={d.name} fill={COLORS[d.name]} />)}</Pie>
      <Tooltip {...tip} /><Legend />
    </PieChart></ResponsiveContainer>
  );
}

export const DailyBar = ({ data }) => (
  <ResponsiveContainer width="100%" height={240}><BarChart data={data}>
    <CartesianGrid stroke="rgba(255,255,255,.06)" /><XAxis dataKey="date" tickFormatter={short} {...axis} /><YAxis allowDecimals={false} {...axis} />
    <Tooltip {...tip} /><Bar dataKey="messages" fill="#22d3ee" radius={[6, 6, 0, 0]} />
  </BarChart></ResponsiveContainer>
);

export const ThreatLine = ({ data }) => (
  <ResponsiveContainer width="100%" height={240}><LineChart data={data}>
    <CartesianGrid stroke="rgba(255,255,255,.06)" /><XAxis dataKey="date" tickFormatter={short} {...axis} /><YAxis allowDecimals={false} {...axis} />
    <Tooltip {...tip} /><Legend />
    {["SAFE", "SPAM", "PHISHING"].map((k) => <Line key={k} type="monotone" dataKey={k} stroke={COLORS[k]} strokeWidth={2} dot={false} />)}
  </LineChart></ResponsiveContainer>
);

export function MetricsBar({ metrics }) {
  if (!metrics) return <Empty text="No trained model metrics available" />;
  const data = [{ name: "Accuracy", v: metrics.accuracy }, { name: "Precision", v: metrics.macro_precision }, { name: "Recall", v: metrics.macro_recall }, { name: "F1", v: metrics.macro_f1 }]
    .map((d) => ({ ...d, v: +(d.v * 100).toFixed(2) }));
  return (
    <ResponsiveContainer width="100%" height={240}><BarChart data={data}>
      <CartesianGrid stroke="rgba(255,255,255,.06)" /><XAxis dataKey="name" {...axis} /><YAxis domain={[0, 100]} {...axis} unit="%" />
      <Tooltip {...tip} /><Bar dataKey="v" fill="#a855f7" radius={[6, 6, 0, 0]} />
    </BarChart></ResponsiveContainer>
  );
}

export function ConfusionMatrix({ cm }) {
  if (!cm) return null;
  const max = Math.max(1, ...cm.matrix.flat());
  return (
    <div className="overflow-x-auto"><table className="text-sm mx-auto">
      <thead><tr><th className="p-2 text-xs text-slate-400">actual ↓ / predicted →</th>{cm.labels.map((l) => <th key={l} className="p-2 text-xs">{l}</th>)}</tr></thead>
      <tbody>{cm.matrix.map((row, i) => (
        <tr key={i}><th className="p-2 text-xs text-left">{cm.labels[i]}</th>{row.map((v, j) => (
          <td key={j} className="p-3 text-center font-mono rounded" style={{ background: `rgba(${i === j ? "34,211,238" : "244,63,94"},${(v / max) * 0.6})` }}>{v}</td>))}</tr>))}</tbody>
    </table></div>
  );
}

export const Empty = ({ text }) => <div className="h-[240px] grid place-items-center text-sm text-slate-500">{text}</div>;
