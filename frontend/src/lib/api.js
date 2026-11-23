
export const getToken = () => localStorage.getItem("sm_token");

export const setToken = (t) =>
  t
    ? localStorage.setItem("sm_token", t)
    : localStorage.removeItem("sm_token");

const API_BASE = (
  import.meta.env.VITE_API_BASE_URL ||
  "https://faithful-appreciation-production-d7b52e4f.up.railway.app"
).replace(/\/+$/, "");

export async function api(path, { method = "GET", body } = {}) {
  const res = await fetch(`${API_BASE}/api${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(getToken()
        ? { Authorization: `Bearer ${getToken()}` }
        : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  let data = null;

  try {
    data = await res.json();
  } catch {
    /* empty body */
  }

  if (!res.ok) {
    const d = data?.detail;
    const msg =
      typeof d === "string"
        ? d
        : Array.isArray(d)
          ? d.map((x) => x.msg).join("; ")
          : `Request failed (${res.status})`;

    const err = new Error(msg);
    err.status = res.status;
    throw err;
  }

  return data;
}

export const wsUrl = () =>
  `${API_BASE.replace(/^http/, "ws")}/ws?token=${encodeURIComponent(getToken())}`;

export const fmtTime = (iso) =>
  iso
    ? new Date(iso).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      })
    : "";

export const fmtDateTime = (iso) =>
  iso ? new Date(iso).toLocaleString() : "—";
