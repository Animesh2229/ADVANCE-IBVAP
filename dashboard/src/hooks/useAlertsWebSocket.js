import { useEffect, useRef, useState, useCallback } from "react";

/**
 * Real-time alerts via WebSocket with polling fallback.
 * Auth: httpOnly cookie (credentials: include).
 */
export function useAlertsWebSocket() {
  const [alerts, setAlerts] = useState([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const pollRef = useRef(null);

  const fetchAlerts = useCallback(async () => {
    try {
      const base = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
      const res = await fetch(`${base}/alerts?limit=40`, { credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        setAlerts(data);
      }
    } catch (e) {
      console.warn("Polling failed", e);
    }
  }, []);

  useEffect(() => {
    fetchAlerts();

    const wsBase = (import.meta.env.VITE_API_URL || "http://localhost:8000")
      .replace("http", "ws")
      .replace("/api/v1", "");
    const wsUrl = `${wsBase}/ws/alerts`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        if (pollRef.current) {
          clearInterval(pollRef.current);
          pollRef.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === "new_alert" && msg.data) {
            setAlerts((prev) => [msg.data, ...prev].slice(0, 50));
          }
        } catch (_) {}
      };

      ws.onclose = () => {
        setConnected(false);
        if (!pollRef.current) {
          pollRef.current = setInterval(fetchAlerts, 5000);
        }
      };

      ws.onerror = () => {
        setConnected(false);
        ws.close();
      };
    } catch (e) {
      pollRef.current = setInterval(fetchAlerts, 5000);
    }

    return () => {
      if (wsRef.current) wsRef.current.close();
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [fetchAlerts]);

  return { alerts, connected, refresh: fetchAlerts };
}
