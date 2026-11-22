import { motion } from "framer-motion";
import { ShieldCheck } from "lucide-react";

export default function AuthShell({ title, subtitle, children }) {
  return (
    <div className="min-h-screen grid place-items-center p-4">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass w-full max-w-md p-8">
        <div className="flex items-center gap-2 text-xl font-bold mb-1"><ShieldCheck className="text-neon-cyan" /> Cipher<span className="text-neon-purple">Chain</span></div>
        <h1 className="text-2xl font-bold mt-4">{title}</h1>
        <p className="text-slate-400 text-sm mb-6">{subtitle}</p>
        {children}
      </motion.div>
    </div>
  );
}
