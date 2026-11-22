import { useCallback, useEffect, useState } from "react";
import { Link2, RefreshCw } from "lucide-react";
import { Banner, Card, ChainBadge, PageTitle, Short } from "../components/ui";
import { ChainViz } from "../components/Visuals";
import { api, fmtDateTime } from "../lib/api";

export default function BlockchainPage() {
  const [status, setStatus] = useState(null); const [records, setRecords] = useState([]);
  const [results, setResults] = useState({}); const [busy, setBusy] = useState(false); const [note, setNote] = useState("");
  const load = useCallback(async () => {
    setStatus(await api("/blockchain/status").catch((e) => ({ connected: false, error: e.message })));
    setRecords(await api("/blockchain/records").catch(() => []));
  }, []);
  useEffect(() => { load(); const t = setInterval(load, 10000); return () => clearInterval(t); }, [load]);

  const verify = async (id) => { const r = await api(`/blockchain/verify/${id}`); setResults((x) => ({ ...x, [id]: r })); load(); };
  const retry = async () => { setBusy(true); try { const r = await api("/blockchain/retry", { method: "POST" }); setNote(`Recorded ${r.recorded} pending message(s).`); load(); } finally { setBusy(false); } };

  return (
    <>
      <PageTitle title="Blockchain Verification" subtitle="SHA-256 hashes of encrypted payloads are stored on a local Ethereum (Hardhat) chain. Verification compares against the live contract." icon={Link2} />
      {status && !status.connected && <Banner tone="red">Blockchain node/contract unavailable: {status.error}. Messages are still delivered, but their integrity record is marked FAILED and verification shows UNAVAILABLE — nothing is simulated.</Banner>}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[["Network", status?.connected ? `chain ${status.chain_id}` : "offline"], ["Latest block", status?.block_number ?? "—"], ["Records on-chain", status?.total_records ?? "—"], ["Contract", status?.contract_address ? `${status.contract_address.slice(0, 8)}…${status.contract_address.slice(-4)}` : "—"]].map(([l, v]) => (
          <Card key={l}><div className="text-xs uppercase text-slate-400">{l}</div><div className="text-xl font-bold mt-1 font-mono">{v}</div></Card>))}
      </div>
      <Card className="mt-4"><h3 className="font-semibold mb-3">Transaction chain</h3><ChainViz records={records} /></Card>
      <Card className="mt-4">
        <div className="flex items-center justify-between mb-3"><h3 className="font-semibold">Message integrity records</h3>
          <button className="btn-ghost text-xs" onClick={retry} disabled={busy}><RefreshCw size={14} /> Record pending</button></div>
        {note && <div className="text-xs text-emerald-300 mb-2">{note}</div>}
        <div className="overflow-x-auto"><table className="w-full text-sm">
          <thead className="text-xs text-slate-400 text-left"><tr><th className="p-2">Msg</th><th>Payload hash</th><th>Tx</th><th>Block</th><th>Recorded</th><th>Last check</th><th /></tr></thead>
          <tbody>{records.map((r) => { const v = results[r.message_id]; return (
            <tr key={r.message_id} className="border-t border-white/5 align-top">
              <td className="p-2">#{r.message_id}</td><td><Short s={r.payload_hash} n={8} /></td><td><Short s={r.tx_hash} n={8} /></td><td>{r.block_number ?? "—"}</td>
              <td><ChainBadge status={r.status} /></td>
              <td>{v ? <ChainBadge status={v.status} /> : r.last_status ? <ChainBadge status={r.last_status} /> : <span className="text-slate-500">—</span>}<div className="text-[10px] text-slate-500">{fmtDateTime(r.last_verified_at)}</div></td>
              <td><button className="btn-ghost text-xs" onClick={() => verify(r.message_id)}>Verify now</button>
                {v?.status === "TAMPERED" && <div className="text-[10px] text-red-300 mt-1">recomputed <Short s={v.recomputed_hash} n={6} /> ≠ on-chain <Short s={v.onchain_hash} n={6} /></div>}</td>
            </tr>); })}</tbody></table>
          {!records.length && <div className="text-sm text-slate-500 p-3">No messages yet.</div>}</div>
      </Card>
    </>
  );
}
