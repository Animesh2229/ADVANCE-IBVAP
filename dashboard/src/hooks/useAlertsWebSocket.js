import { useEffect, useRef, useState, useCallback } from "react";

/**
 * Real-time alerts via WebSocket with robust reconnect + polling fallback.
 * Auth: httpOnly cookie (credentials: include) — browsers send cookies on same-origin WS.
 * Also supports optional short-lived ?token= if provided by env/localStorage (future).
 */
export function useAlertsWebSocket() {
  const [alerts, setAlerts] = useState([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const pollRef = useRef(null);
  const retryRef = useRef(0);
  const mountedRef = useRef(true);

  const fetchAlerts = useCallback(async () => {
    try {
      const base = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
      const res = await fetch(`${base}/alerts?limit=40`, { credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        if (mountedRef.current) setAlerts(data);
      }
    } catch (e) {
      console.warn("Polling failed", e);
    }
  }, []);

  const startPolling = useCallback(() => {
    if (!pollRef.current) {
      pollRef.current = setInterval(fetchAlerts, 5000);
    }
  }, [fetchAlerts]);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    fetchAlerts();

    let reconnectTimer = null;

    const connect = () => {
      if (!mountedRef.current) return;

      const wsBase = (import.meta.env.VITE_API_URL || "http://localhost:8000")
        .replace(/^http/, "ws")
        .replace(/\/api\/v1\/?$/, "");

      // Optional explicit token (if ever stored); primary path is cookie
      let tokenPart = "";
      try {
        const t = localStorage.getItem("ibvap_ws_token");
        if (t) tokenPart = `?token=${encodeURIComponent(t)}`;
      } catch (_) {}

      const wsUrl = `${wsBase}/ws/alerts${tokenPart}`;

      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          if (!mountedRef.current) return;
          setConnected(true);
          retryRef.current = 0;
          stopPolling();
        };

        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);
            if (msg.type === "new_alert" && msg.data) {
              setAlerts((prev) => [msg.data, ...prev].slice(0, 50));
            }
          } catch (_) {}
        };

        ws.onclose = (ev) => {
          if (!mountedRef.current) return;
          setConnected(false);
          startPolling();
          // Exponential backoff reconnect (max ~30s)
          const delay = Math.min(1000 * 2 ** retryRef.current, 30000);
          retryRef.current += 1;
          reconnectTimer = setTimeout(connect, delay);
        };

        ws.onerror = () => {
          try { ws.close(); } catch (_) {}
        };
      } catch (e) {
        startPolling();
        const delay = Math.min(1000 * 2 ** retryRef.current, 30000);
        retryRef.current += 1;
        reconnectTimer = setTimeout(connect, delay);
      }
    };

    connect();

    return () => {
      mountedRef.current = false;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (wsRef.current) {
        try { wsRef.current.close(); } catch (_) {}
      }
      stopPolling();
    };
  }, [fetchAlerts, startPolling, stopPolling]);

  return { alerts, connected, refresh: fetchAlerts };
}
