import { useEffect, useState } from "react";
import api from "../api/axios";
import Navbar from "../components/Navbar";

export default function Reports() {
  const [stats, setStats] = useState({ total: 0, intrusion: 0, detection: 0 });

  useEffect(() => {
    api.get("/alerts?limit=1000").then((res) => {
      const data = res.data || [];
      setStats({
        total: data.length,
        intrusion: data.filter(a => a.alert_type === "INTRUSION").length,
        detection: data.filter(a => a.alert_type === "DETECTION").length,
      });
    }).catch(console.error);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950">
      <Navbar />
      <div className="p-6 max-w-5xl mx-auto">
        <h1 className="text-white text-2xl font-bold mb-6">Reports</h1>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-6">
            <p className="text-slate-400">Total Alerts</p>
            <p className="text-3xl text-white font-bold mt-2">{stats.total}</p>
          </div>
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-6">
            <p className="text-slate-400">Intrusions</p>
            <p className="text-3xl text-red-400 font-bold mt-2">{stats.intrusion}</p>
          </div>
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-6">
            <p className="text-slate-400">Detections</p>
            <p className="text-3xl text-blue-400 font-bold mt-2">{stats.detection}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
