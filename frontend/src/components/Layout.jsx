import { NavLink, Outlet } from "react-router-dom";
import { BarChart3, Brain, LayoutDashboard, Link2, LogOut, MessageSquare, Settings, ShieldCheck } from "lucide-react";
import { useAuth } from "../context/AuthContext";

const NAV = [
  ["/", "Dashboard", LayoutDashboard], ["/chat", "Secure Chat", MessageSquare], ["/threats", "AI Threats", Brain],
  ["/blockchain", "Blockchain", Link2], ["/analytics", "Analytics", BarChart3], ["/settings", "Settings", Settings],
];

export default function Layout() {
  const { user, logout } = useAuth();
  const link = ({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition ${isActive ? "bg-neon-cyan/10 text-neon-cyan border border-neon-cyan/30" : "text-slate-300 hover:bg-white/5 border border-transparent"}`;
  return (
    <div className="min-h-screen md:flex">
      <aside className="hidden md:flex md:w-64 shrink-0 flex-col gap-2 p-4 glass rounded-none border-y-0 border-l-0 sticky top-0 h-screen">
        <div className="flex items-center gap-2 px-2 py-3 text-lg font-bold"><ShieldCheck className="text-neon-cyan" /> Cipher<span className="text-neon-purple">Chain</span></div>
        {NAV.map(([to, label, Icon]) => <NavLink key={to} to={to} end={to === "/"} className={link}><Icon size={18} />{label}</NavLink>)}
        <div className="mt-auto glass p-3 text-xs">
          <div className="font-semibold text-sm truncate">{user.display_name}</div>
          <div className="text-slate-400 truncate">@{user.username}</div>
          <button onClick={logout} className="btn-ghost w-full mt-3"><LogOut size={14} /> Sign out</button>
        </div>
      </aside>
      <main className="flex-1 min-w-0 p-4 md:p-8 pb-24 md:pb-8"><Outlet /></main>
      <nav className="md:hidden fixed bottom-0 inset-x-0 z-20 glass rounded-none border-x-0 border-b-0 flex justify-around py-2">
        {NAV.map(([to, label, Icon]) => (
          <NavLink key={to} to={to} end={to === "/"} aria-label={label} className={({ isActive }) => `p-2 rounded-lg ${isActive ? "text-neon-cyan" : "text-slate-400"}`}><Icon size={22} /></NavLink>
        ))}
      </nav>
    </div>
  );
}
