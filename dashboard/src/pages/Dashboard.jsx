import { useMemo, useState } from "react";
import Navbar from "../components/Navbar";
import { Activity, AlertTriangle, Camera, Wifi, WifiOff } from "lucide-react";
import { useAlertsWebSocket } from "../hooks/useAlertsWebSocket";

function bopFromCamera(cameraId) {
  if (!cameraId) return "UNKNOWN";
  if (cameraId.includes("-CAM")) return cameraId.split("-CAM")[0];
  const parts = cameraId.split("-");
  return parts.length >= 2 ? parts.slice(0, 2).join("-") : cameraId;
}

export default function Dashboard() {
  const token = localStorage.getItem("token");
  const { alerts, connected, refresh } = useAlertsWebSocket(token);
  const [bopFilter, setBopFilter] = useState("ALL");

  const bops = useMemo(() => {
    const s = new Set();
    alerts.forEach((a) => s.add(bopFromCamera(a.camera_id)));
    return Array.from(s).sort();
  }, [alerts]);

  const filtered = useMemo(() => {
    if (bopFilter === "ALL") return alerts;
    return alerts.filter((a) => bopFromCamera(a.camera_id) === bopFilter);
  }, [alerts, bopFilter]);

  return (
    <div className="min-h-screen bg-slate-950">
      <Navbar />
      <div className="p-6 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-4 flex items-center gap-4">
            <AlertTriangle className="text-red-400" />
            <div>
              <p className="text-slate-400 text-sm">Active Alerts</p>
              <p className="text-white text-xl font-semibold">{filtered.length}</p>
            </div>
          </div>
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-4 flex items-center gap-4">
            <Camera className="text-blue-400" />
            <div>
              <p className="text-slate-400 text-sm">BOPs in view</p>
              <p className="text-white text-xl font-semibold">{bops.length || "—"}</p>
            </div>
          </div>
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-4 flex items-center gap-4">
            <Activity className="text-emerald-400" />
            <div>
              <p className="text-slate-400 text-sm">Status</p>
              <p className="text-white text-xl font-semibold">Live</p>
            </div>
          </div>
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-4 flex items-center gap-4">
            {connected ? <Wifi className="text-emerald-400" /> : <WifiOff className="text-amber-400" />}
            <div>
              <p className="text-slate-400 text-sm">Realtime</p>
              <p className="text-white text-xl font-semibold">{connected ? "WebSocket" : "Polling"}</p>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 mb-4">
          <label className="text-slate-400 text-sm">BOP filter</label>
          <select
            value={bopFilter}
            onChange={(e) => setBopFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm"
          >
            <option value="ALL">All BOPs ({bops.length || 0})</option>
            {bops.map((b) => (
              <option key={b} value={b}>{b}</option>
            ))}
          </select>
          <button onClick={refresh} className="text-sm text-blue-400 hover:text-blue-300 ml-auto">
            Refresh
          </button>
        </div>

        <div className="bg-slate-900 border border-slate-700 rounded-xl p-5">
          <h2 className="text-white font-semibold text-lg mb-4">Live Alerts</h2>
          {filtered.length === 0 ? (
            <p className="text-slate-400">No alerts yet. Waiting for edge devices...</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filtered.map((alert) => (
                <div
                  key={alert.id || Math.random()}
                  className={`bg-slate-800 border border-slate-700 rounded-lg p-4 border-l-4 ${
                    alert.priority === "HIGH" ? "border-l-red-500" : "border-l-blue-500"
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-white font-medium">
                        {alert.alert_type} {alert.subtype ? `• ${alert.subtype}` : ""}
                      </p>
                      <p className="text-slate-400 text-sm mt-1">
                        {bopFromCamera(alert.camera_id)} · {alert.camera_id}
                      </p>
                    </div>
                    <span className="text-xs bg-slate-700 text-slate-300 px-2 py-1 rounded">
                      {alert.confidence ? (alert.confidence * 100).toFixed(0) + "%" : "-"}
                    </span>
                  </div>
                  <div className="flex justify-between items-center mt-3 text-xs text-slate-500">
                    <span>{alert.timestamp ? new Date(alert.timestamp).toLocaleString() : ""}</span>
                    <span className="capitalize">{alert.status || "new"}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
