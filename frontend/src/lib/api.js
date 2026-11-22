export const getToken = () => localStorage.getItem("sm_token");
export const setToken = (t) => (t ? localStorage.setItem("sm_token", t) : localStorage.removeItem("sm_token"));

export async function api(path, { method = "GET", body } = {}) {
  const res = await fetch(`/api${path}`, {
    method,
    headers: { "Content-Type": "application/json", ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = null;
  try { data = await res.json(); } catch { /* empty body */ }
  if (!res.ok) {
    const d = data?.detail;
    const msg = typeof d === "string" ? d : Array.isArray(d) ? d.map((x) => x.msg).join("; ") : `Request failed (${res.status})`;
    const err = new Error(msg); err.status = res.status; throw err;
  }
  return data;
}

export const wsUrl = () => `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws?token=${encodeURIComponent(getToken())}`;
export const fmtTime = (iso) => (iso ? new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "");
export const fmtDateTime = (iso) => (iso ? new Date(iso).toLocaleString() : "—");
