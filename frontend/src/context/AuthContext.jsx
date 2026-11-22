import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, getToken, setToken } from "../lib/api";
import { generateKeyPair } from "../lib/e2ee";
import { loadKey, saveKey } from "../lib/keystore";

const Ctx = createContext(null);
export const useAuth = () => useContext(Ctx);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [identity, setIdentity] = useState(null); // { privateKey, publicKeyB64 } from this browser
  const [loading, setLoading] = useState(!!getToken());

  const attach = useCallback(async (u) => {
    setUser(u);
    const stored = await loadKey(u.id).catch(() => null);
    setIdentity(stored && stored.publicKeyB64 === u.public_key ? stored : null); // null => cannot decrypt on this browser
  }, []);

  useEffect(() => {
    if (!getToken()) return;
    api("/users/me").then(attach).catch(() => setToken(null)).finally(() => setLoading(false));
  }, [attach]);

  const login = async (username, password) => {
    const r = await api("/auth/login", { method: "POST", body: { username, password } });
    setToken(r.token); await attach(r.user);
  };

  const register = async (form) => {
    const kp = await generateKeyPair(false); // private key is NON-extractable
    const r = await api("/auth/register", { method: "POST", body: { ...form, public_key: kp.publicKeyB64 } });
    setToken(r.token);
    await saveKey(r.user.id, kp.privateKey, kp.publicKeyB64);
    await attach(r.user);
  };

  const rotateKey = async () => {
    const kp = await generateKeyPair(false);
    const u = await api("/users/me/public-key", { method: "PUT", body: { public_key: kp.publicKeyB64 } });
    await saveKey(u.id, kp.privateKey, kp.publicKeyB64);
    await attach(u);
  };

  const logout = () => { setToken(null); setUser(null); setIdentity(null); };
  const updateUser = (u) => setUser(u);

  return <Ctx.Provider value={{ user, identity, loading, login, register, logout, rotateKey, updateUser }}>{children}</Ctx.Provider>;
}
