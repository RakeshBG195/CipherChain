import { useEffect, useState } from "react";
import { api } from "./api";

export function useSummary(intervalMs = 8000) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let alive = true;
    const load = () => api("/dashboard/summary").then((d) => alive && (setData(d), setError(""))).catch((e) => alive && setError(e.message));
    load(); const t = setInterval(load, intervalMs);
    return () => { alive = false; clearInterval(t); };
  }, [intervalMs]);
  return { data, error };
}
