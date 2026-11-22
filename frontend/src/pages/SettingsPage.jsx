import { useEffect, useState } from "react";
import { KeyRound, Settings } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { Banner, Card, ErrorText, PageTitle } from "../components/ui";
import { api } from "../lib/api";
import { fingerprint } from "../lib/e2ee";

export default function SettingsPage() {
  const { user, identity, updateUser, rotateKey, logout } = useAuth();
  const [f, setF] = useState({ display_name: user.display_name, bio: user.bio || "" });
  const [fp, setFp] = useState(""); const [msg, setMsg] = useState(""); const [err, setErr] = useState("");
  useEffect(() => { fingerprint(user.public_key).then(setFp); }, [user.public_key]);

  const save = async (e) => { e.preventDefault(); setErr(""); try { updateUser(await api("/users/me", { method: "PUT", body: f })); setMsg("Profile saved."); } catch (x) { setErr(x.message); } };
  const rotate = async () => {
    if (!window.confirm("Generate a NEW identity key? Messages encrypted to your old key will become unreadable.")) return;
    setErr(""); try { await rotateKey(); setMsg("New identity key generated and published."); } catch (x) { setErr(x.message); }
  };
  return (
    <>
      <PageTitle title="Settings" subtitle="Profile and encryption identity" icon={Settings} />
      {!identity && <Banner tone="red">This browser does not hold the private key for your published public key.</Banner>}
      <div className="grid lg:grid-cols-2 gap-4">
        <Card>
          <h3 className="font-semibold mb-3">Profile</h3>
          <form onSubmit={save} className="space-y-3">
            <div><label className="label">Username</label><input className="input opacity-60" value={`@${user.username}`} disabled /></div>
            <div><label className="label">Display name</label><input className="input" value={f.display_name} onChange={(e) => setF({ ...f, display_name: e.target.value })} required /></div>
            <div><label className="label">Bio</label><textarea className="input h-20" maxLength={280} value={f.bio} onChange={(e) => setF({ ...f, bio: e.target.value })} /></div>
            <button className="btn-primary">Save profile</button>
          </form>
        </Card>
        <Card>
          <h3 className="font-semibold mb-3 flex items-center gap-2"><KeyRound size={16} className="text-neon-purple" /> Encryption identity</h3>
          <div className="text-xs text-slate-400">Public key fingerprint (SHA-256)</div>
          <div className="font-mono text-sm break-all mb-3">{fp}</div>
          <p className="text-xs text-slate-400 mb-3">The private key is a non-extractable WebCrypto key stored in this browser's IndexedDB. The server and the blockchain only ever see the public key and ciphertext hashes. Clearing browser data or using another device means you need a new key.</p>
          <button className="btn-ghost" onClick={rotate}>Generate new identity key</button>
          <div className="mt-6"><button className="btn-ghost text-red-300" onClick={logout}>Sign out</button></div>
        </Card>
      </div>
      <div className="mt-3 space-y-1"><ErrorText error={err} />{msg && <div className="text-sm text-emerald-300">{msg}</div>}</div>
    </>
  );
}
