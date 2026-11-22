import { AnimatePresence, motion } from "framer-motion";
import { Box, KeyRound, Link2, Lock, ShieldCheck, Type } from "lucide-react";
import { Short } from "./ui";

/** Animated pipeline built from the REAL values of the last message encrypted in this session. */
export function EncryptionViz({ trace }) {
  if (!trace) return <div className="text-sm text-slate-500">Send a message to see its real encryption pipeline here.</div>;
  const steps = [
    [Type, "Plaintext (stays in your browser)", trace.plaintext, "text-slate-200"],
    [KeyRound, "ECDH P-256 → HKDF-SHA256 → AES-256 session key", `key fingerprint ${trace.keyFp}`, "text-neon-purple"],
    [Lock, "AES-256-GCM  ·  96-bit random nonce", `nonce ${trace.nonce}`, "text-neon-cyan"],
    [Box, "Ciphertext + 128-bit auth tag (sent to server)", trace.ciphertext.slice(0, 64) + (trace.ciphertext.length > 64 ? "…" : ""), "text-neon-blue"],
    [Link2, "SHA-256 payload hash (recorded on-chain)", trace.hash, "text-emerald-300"],
  ];
  return (
    <div className="space-y-2">
      <AnimatePresence mode="popLayout">
        {steps.map(([Icon, title, val, cls], i) => (
          <motion.div key={trace.hash + i} initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.25 }} className="glass p-3">
            <div className={`flex items-center gap-2 text-xs font-semibold ${cls}`}><Icon size={14} />{title}</div>
            <div className="font-mono text-[11px] text-slate-300 break-all mt-1">{val}</div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}

/** Chain of real on-chain records (tx hash / block). */
export function ChainViz({ records }) {
  const items = (records || []).filter((r) => r.status === "RECORDED").slice(0, 6).reverse();
  if (!items.length) return <div className="text-sm text-slate-500">No on-chain records yet.</div>;
  return (
    <div className="flex gap-3 overflow-x-auto pb-2">
      {items.map((r, i) => (
        <motion.div key={r.message_id} initial={{ opacity: 0, scale: 0.85 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.12 }} className="flex items-center gap-3 shrink-0">
          <div className="glass p-3 w-48 border-neon-cyan/30">
            <div className="text-xs text-neon-cyan flex items-center gap-1"><ShieldCheck size={12} /> Block #{r.block_number}</div>
            <div className="text-[11px] mt-1 text-slate-400">tx <Short s={r.tx_hash} n={8} /></div>
            <div className="text-[11px] text-slate-400">hash <Short s={r.payload_hash} n={8} /></div>
          </div>
          {i < items.length - 1 && <motion.div animate={{ opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 1.6 }} className="text-neon-purple">→</motion.div>}
        </motion.div>
      ))}
    </div>
  );
}
