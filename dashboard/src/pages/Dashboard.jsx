import Navbar from "../components/Navbar";
import { Activity, AlertTriangle, Camera, Wifi, WifiOff } from "lucide-react";
import { useAlertsWebSocket } from "../hooks/useAlertsWebSocket";

export default function Dashboard() {
  const token = localStorage.getItem("token");
  const { alerts, connected, refresh } = useAlertsWebSocket(token);

  return (
    <div className="min-h-screen bg-slate-950">
      <Navbar />
      <div className="p-6 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-4 flex items-center gap-4">
            <AlertTriangle className="text-red-400" />
            <div>
              <p className="text-slate-400 text-sm">Active Alerts</p>
              <p className="text-white text-xl font-semibold">{alerts.length}</p>
            </div>
          </div>
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-4 flex items-center gap-4">
            <Camera className="text-blue-400" />
            <div>
              <p className="text-slate-400 text-sm">System</p>
              <p className="text-white text-xl font-semibold">Operational</p>
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

        <div className="bg-slate-900 border border-slate-700 rounded-xl p-5">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-white font-semibold text-lg">Live Alerts</h2>
            <button onClick={refresh} className="text-sm text-blue-400 hover:text-blue-300">
              Refresh
            </button>
          </div>

          {alerts.length === 0 ? (
            <p className="text-slate-400">No alerts yet. Waiting for edge devices...</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {alerts.map((alert) => (
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
                      <p className="text-slate-400 text-sm mt-1">Camera: {alert.camera_id}</p>
                    </div>
                    <span className="text-xs bg-slate-700 text-slate-300 px-2 py-1 rounded">
                      {alert.confidence ? (alert.confidence * 100).toFixed(0) + "%" : "-"}
                    </span>
                  </div>
                  <div className="flex justify-between items-center mt-3 text-xs text-slate-500">
                    <span>
                      {alert.timestamp ? new Date(alert.timestamp).toLocaleString() : ""}
                    </span>
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
