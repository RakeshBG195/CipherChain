
import { useCallback, useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Check, CheckCheck, Lock, Search, Send, ShieldAlert } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { Banner, CategoryBadge, ChainBadge, ErrorText } from "../components/ui";
import { EncryptionViz } from "../components/Visuals";
import { api, fmtTime, wsUrl } from "../lib/api";
import { decryptMessage, deriveConversationKey, encryptMessage, fingerprint, payloadHash } from "../lib/e2ee";

const Ticks = ({ status }) => status === "sent" ? <Check size={14} className="text-slate-400" /> : <CheckCheck size={14} className={status === "read" ? "text-neon-cyan" : "text-slate-400"} />;

function Bubble({ m, mine }) {
  const risky = m.scan && m.scan.category !== "SAFE" && !mine;
  const [show, setShow] = useState(!risky);
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className={`flex ${mine ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[85%] md:max-w-[70%] rounded-2xl px-3 py-2 border ${mine ? "bg-neon-blue/20 border-neon-blue/30" : "bg-white/5 border-white/10"} ${risky ? "border-red-400/50" : ""}`}>
        {risky && <div className="flex items-center gap-2 text-xs text-red-300 mb-1"><ShieldAlert size={14} /> {m.scan.category} detected Â· risk {m.scan.risk_score}</div>}
        {!m.decOk ? <div className="text-sm text-red-300 flex items-center gap-1"><Lock size={14} /> Could not decrypt â€” payload invalid or modified</div>
          : show ? <div className="text-sm whitespace-pre-wrap break-words">{m.plain}</div>
          : <button className="text-xs underline text-slate-300" onClick={() => setShow(true)}>Show flagged message</button>}
        <div className="flex flex-wrap items-center justify-end gap-2 mt-1 text-[10px] text-slate-400">
          {m.chain ? <ChainBadge status={m.chain.status} /> : <ChainBadge status="PENDING" />}
          {!mine && m.scan && !risky && <CategoryBadge category={m.scan.category} />}
          <span>{fmtTime(m.created_at)}</span>{mine && <Ticks status={m.status} />}
        </div>
      </div>
    </motion.div>
  );
}

export default function Chat() {
  const { user, identity } = useAuth();
  const [convs, setConvs] = useState([]);
  const [active, setActive] = useState(null);
  const [msgs, setMsgs] = useState([]);
  const [text, setText] = useState("");
  const [q, setQ] = useState("");
  const [found, setFound] = useState([]);
  const [trace, setTrace] = useState(null);
  const [err, setErr] = useState("");
  const [wsUp, setWsUp] = useState(false);

  const keys = useRef({});
  const activeRef = useRef(null);
  const handler = useRef(() => {});
  const endRef = useRef(null);
  activeRef.current = active;

  const refreshConvs = useCallback(() => api("/conversations").then((c) => {
    setConvs(c);
    setActive((a) => a && (c.find((x) => x.id === a.id) || a));
  }).catch((e) => setErr(e.message)), []);

  const getKey = useCallback(async (conv) => {
    if (!identity) return null;
    const k = `${conv.id}:${conv.peer.public_key}`;
    if (!keys.current[k]) {
      keys.current[k] = await deriveConversationKey(identity.privateKey, user.public_key, conv.peer.public_key, conv.id);
    }
    return keys.current[k];
  }, [identity, user]);

  const process = useCallback(async (conv, m) => {
    const key = await getKey(conv);
    let plain = null;
    let decOk = false;

    if (key) {
      try {
        plain = await decryptMessage(key, m.nonce, m.ciphertext, conv.id, m.sender_id);
        decOk = true;
      } catch {
        /* auth tag mismatch */
      }
    }

    let chain;
    try {
      const v = await api(`/blockchain/verify/${m.id}`);
      const local = await payloadHash(conv.id, m.sender_id, m.nonce, m.ciphertext);
      let status = v.status;
      if (status === "VERIFIED" && (!v.onchain_hash || v.onchain_hash.toLowerCase() !== local)) {
        status = "TAMPERED";
      }
      chain = { status, tx: v.tx_hash, block: v.block_number };
    } catch {
      chain = { status: "UNAVAILABLE" };
    }

    let scan = m.scan;
    if (decOk && !scan && m.sender_id !== user.id) {
      try {
        const r = await api("/ai/analyze", {
          method: "POST",
          body: { text: plain, message_id: m.id }
        });
        scan = {
          category: r.category,
          risk_score: r.risk_score,
          confidence: r.confidence
        };
      } catch {
        /* model unavailable */
      }
    }

    return { ...m, plain, decOk, chain, scan };
  }, [getKey, user]);

  const openConv = useCallback(async (conv) => {
    setActive(conv);
    setMsgs([]);
    setErr("");

    try {
      const raw = await api(`/conversations/${conv.id}/messages`);
      setMsgs(await Promise.all(raw.map((m) => process(conv, m))));
      await api(`/conversations/${conv.id}/read`, { method: "POST" });
      refreshConvs();
    } catch (e) {
      setErr(e.message);
    }
  }, [process, refreshConvs]);

  handler.current = async (ev) => {
    if (ev.type === "message.new") {
      const conv = convs.find((c) => c.id === ev.message.conversation_id);

      if (conv && activeRef.current?.id === conv.id) {
        const pm = await process(conv, ev.message);
        setMsgs((x) => x.some((y) => y.id === pm.id) ? x : [...x, pm]);
        api(`/conversations/${conv.id}/read`, { method: "POST" });
      }

      refreshConvs();
    } else if (ev.type === "message.status") {
      setMsgs((x) => x.map((m) => (
        m.id === ev.message_id && m.status !== "read"
          ? { ...m, status: ev.status }
          : m
      )));
    } else if (ev.type === "message.read") {
      setMsgs((x) => x.map((m) => (
        ev.message_ids.includes(m.id) ? { ...m, status: "read" } : m
      )));
    } else if (ev.type === "presence") {
      setConvs((cs) => cs.map((c) => (
        c.peer.id === ev.user_id
          ? { ...c, peer: { ...c.peer, is_online: ev.is_online, last_seen: ev.last_seen } }
          : c
      )));
      setActive((a) => (
        a && a.peer.id === ev.user_id
          ? { ...a, peer: { ...a.peer, is_online: ev.is_online } }
          : a
      ));
    }
  };

  useEffect(() => {
    refreshConvs();
  }, [refreshConvs]);

  useEffect(() => {
    let ws;
    let stop = false;
    let ping;

    const connect = () => {
      ws = new WebSocket(wsUrl());
      ws.onopen = () => {
        setWsUp(true);
        ping = setInterval(() => ws.readyState === 1 && ws.send("ping"), 25000);
      };
      ws.onmessage = (e) => handler.current(JSON.parse(e.data));
      ws.onclose = () => {
        setWsUp(false);
        clearInterval(ping);
        if (!stop) setTimeout(connect, 2000);
      };
    };

    connect();
    return () => {
      stop = true;
      clearInterval(ping);
      ws && ws.close();
    };
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs]);

  const search = async (v) => {
    setQ(v);
    setFound(v.trim() ? await api(`/users?q=${encodeURIComponent(v)}`).catch(() => []) : []);
  };

  const start = async (u) => {
    const c = await api("/conversations", { method: "POST", body: { peer_id: u.id } });
    setQ("");
    setFound([]);
    await refreshConvs();
    openConv(c);
  };

  const send = async (e) => {
    e.preventDefault();
    const t = text.trim();
    if (!t || !active) return;
    setErr("");

    try {
      const key = await getKey(active);
      const { nonce, ciphertext } = await encryptMessage(key, t, active.id, user.id);
      setText("");

      const saved = await api(`/conversations/${active.id}/messages`, {
        method: "POST",
        body: { nonce, ciphertext }
      });

      setTrace({
        plaintext: t,
        keyFp: `${(await fingerprint(active.peer.public_key)).slice(0, 19)} (peer key)`,
        nonce,
        ciphertext,
        hash: await payloadHash(active.id, user.id, nonce, ciphertext)
      });

      // Display immediately; blockchain recording happens in the background.
      setMsgs((x) => [
        ...x,
        { ...saved, plain: t, decOk: true, chain: null, scan: null }
      ]);

      refreshConvs();
    } catch (x) {
      setErr(x.message);
    }
  };

  return (
    <div>
      {!identity && <Banner tone="red">This browser has no private key matching your account, so messages cannot be encrypted or decrypted here. Open Settings to create a new identity key (older messages will stay unreadable).</Banner>}

      <div className="grid md:grid-cols-[300px_1fr] lg:grid-cols-[300px_1fr_320px] gap-4 h-[calc(100vh-9rem)] md:h-[calc(100vh-6rem)]">
        <aside className={`glass p-3 flex flex-col min-h-0 ${active ? "hidden md:flex" : "flex"}`}>
          <div className="relative mb-3">
            <Search size={14} className="absolute left-3 top-3 text-slate-500" />
            <input className="input pl-8" placeholder="Find a user to chatâ€¦" value={q} onChange={(e) => search(e.target.value)} />
          </div>

          {found.length > 0 && (
            <div className="mb-3 space-y-1">
              {found.map((u) => (
                <button key={u.id} onClick={() => start(u)} className="w-full text-left btn-ghost justify-start text-xs">
                  + {u.display_name} <span className="text-slate-400">@{u.username}</span>
                </button>
              ))}
            </div>
          )}

          <div className="flex-1 overflow-y-auto space-y-1">
            {!convs.length && <div className="text-xs text-slate-500 p-2">No conversations yet. Search for a user above.</div>}

            {convs.map((c) => (
              <button key={c.id} onClick={() => openConv(c)} className={`w-full text-left rounded-xl p-3 border transition ${active?.id === c.id ? "border-neon-cyan/40 bg-neon-cyan/5" : "border-transparent hover:bg-white/5"}`}>
                <div className="flex items-center gap-2">
                  <span className={`h-2 w-2 rounded-full ${c.peer.is_online ? "bg-emerald-400 shadow-[0_0_8px_#34d399]" : "bg-slate-600"}`} />
                  <span className="font-semibold text-sm truncate">{c.peer.display_name}</span>
                  {c.unread > 0 && <span className="ml-auto text-[10px] bg-neon-purple rounded-full px-2">{c.unread}</span>}
                </div>
                <div className="text-[11px] text-slate-500">@{c.peer.username} Â· {c.peer.is_online ? "online" : "offline"}</div>
              </button>
            ))}
          </div>

          <div className="text-[10px] text-slate-500 mt-2">Realtime: {wsUp ? "connected" : "reconnectingâ€¦"}</div>
        </aside>

        <section className={`glass flex flex-col min-h-0 ${active ? "flex" : "hidden md:flex"}`}>
          {!active ? (
            <div className="m-auto text-slate-500 text-sm flex flex-col items-center gap-2">
              <Lock /> Select or start a conversation. Messages are end-to-end encrypted.
            </div>
          ) : (
            <>
              <header className="flex items-center gap-3 p-3 border-b border-white/10">
                <button className="md:hidden" onClick={() => setActive(null)} aria-label="Back"><ArrowLeft /></button>
                <span className={`h-2.5 w-2.5 rounded-full ${active.peer.is_online ? "bg-emerald-400" : "bg-slate-600"}`} />
                <div>
                  <div className="font-semibold text-sm">{active.peer.display_name}</div>
                  <div className="text-[11px] text-slate-400">{active.peer.is_online ? "online" : `last seen ${active.peer.last_seen ? new Date(active.peer.last_seen).toLocaleString() : "never"}`}</div>
                </div>
                <span className="ml-auto text-[11px] text-neon-cyan flex items-center gap-1"><Lock size={12} /> AES-256-GCM E2EE</span>
              </header>

              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {msgs.map((m) => <Bubble key={m.id} m={m} mine={m.sender_id === user.id} />)}
                <div ref={endRef} />
              </div>

              <form onSubmit={send} className="p-3 border-t border-white/10 flex gap-2 items-center">
                <input className="input" placeholder={identity ? "Type an encrypted messageâ€¦" : "Identity key missing"} disabled={!identity} value={text} onChange={(e) => setText(e.target.value)} />
                <button className="btn-primary" disabled={!identity || !text.trim()}><Send size={16} /></button>
              </form>

              <div className="px-3 pb-2"><ErrorText error={err} /></div>
            </>
          )}
        </section>

        <aside className="hidden lg:block glass p-3 overflow-y-auto min-h-0">
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2"><Lock size={14} className="text-neon-cyan" /> Live encryption trace</h3>
          <EncryptionViz trace={trace} />
        </aside>
      </div>
    </div>
  );
}
