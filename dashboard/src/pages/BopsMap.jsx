import { useEffect, useMemo, useState } from "react";
import Navbar from "../components/Navbar";
import api from "../api/axios";
import { bopFromCamera, frontierFromBop, bopPosition, FRONTIERS } from "../utils/bop";

export default function BopsMap() {
  const [alerts, setAlerts] = useState([]);
  const [frontierFilter, setFrontierFilter] = useState("ALL");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await api.get("/alerts?limit=100");
        if (alive) setAlerts(res.data || []);
      } catch (e) {
        console.warn(e);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    const t = setInterval(async () => {
      try {
        const res = await api.get("/alerts?limit=100");
        setAlerts(res.data || []);
      } catch (_) {}
    }, 8000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);

  const bopStats = useMemo(() => {
    const map = {};
    for (const a of alerts) {
      const bop = bopFromCamera(a.camera_id);
      if (!map[bop]) {
        map[bop] = {
          bop,
          sector: frontierFromBop(bop),
          count: 0,
          high: 0,
          ...bopPosition(bop),
        };
      }
      map[bop].count += 1;
      if (a.priority === "HIGH") map[bop].high += 1;
    }
    return Object.values(map);
  }, [alerts]);

  const filtered = useMemo(() => {
    if (frontierFilter === "ALL") return bopStats;
    return bopStats.filter((b) => b.sector === frontierFilter);
  }, [bopStats, frontierFilter]);

  const frontierCounts = useMemo(() => {
    const c = Object.fromEntries(FRONTIERS.map((f) => [f, 0]));
    bopStats.forEach((b) => {
      if (c[b.sector] !== undefined) c[b.sector] += 1;
    });
    return c;
  }, [bopStats]);

  return (
    <div className="min-h-screen bg-slate-950">
      <Navbar />
      <div className="p-6 max-w-7xl mx-auto">
        <div className="flex flex-wrap items-center gap-3 mb-6">
          <h1 className="text-white text-xl font-semibold mr-4">SSB Frontiers \u00b7 BOP Map</h1>
          <select
            value={frontierFilter}
            onChange={(e) => setFrontierFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm"
          >
            <option value="ALL">All Frontiers</option>
            {FRONTIERS.map((s) => (
              <option key={s} value={s}>
                {s} ({frontierCounts[s] || 0})
              </option>
            ))}
          </select>
          <span className="text-slate-500 text-sm ml-auto">
            {filtered.length} active BOP(s) \u00b7 SSB / Police ops
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
          {FRONTIERS.map((s) => (
            <button
              key={s}
              onClick={() => setFrontierFilter(s === frontierFilter ? "ALL" : s)}
              className={`rounded-xl border p-3 text-left transition ${
                frontierFilter === s
                  ? "border-blue-500 bg-slate-800"
                  : "border-slate-700 bg-slate-900 hover:border-slate-500"
              }`}
            >
              <p className="text-slate-400 text-xs">{s} FTR</p>
              <p className="text-white text-lg font-semibold">{frontierCounts[s] || 0} BOPs</p>
            </button>
          ))}
        </div>

        <div className="relative bg-slate-900 border border-slate-700 rounded-xl h-[420px] mb-6 overflow-hidden">
          <div
            className="absolute inset-0 opacity-30"
            style={{
              backgroundImage:
                "linear-gradient(#1e293b 1px, transparent 1px), linear-gradient(90deg, #1e293b 1px, transparent 1px)",
              backgroundSize: "40px 40px",
            }}
          />
          <span className="absolute top-2 left-3 text-slate-600 text-xs">
            West \u2190 Indo-Nepal / Bhutan border belt \u2192 East
          </span>
          <span className="absolute bottom-2 left-3 text-slate-600 text-xs">
            SSB Frontiers (Ranikhet \u2192 Guwahati)
          </span>
          {loading && (
            <p className="absolute inset-0 flex items-center justify-center text-slate-500">Loading\u2026</p>
          )}
          {!loading && filtered.length === 0 && (
            <p className="absolute inset-0 flex items-center justify-center text-slate-500">
              No active BOPs yet \u2014 alerts aane par yahan dikhenge
            </p>
          )}
          {filtered.map((b) => (
            <div
              key={b.bop}
              title={`${b.bop} \u00b7 ${b.sector} \u00b7 ${b.count} alerts`}
              className={`absolute w-3 h-3 rounded-full -translate-x-1/2 -translate-y-1/2 ${
                b.high > 0 ? "bg-red-500 ring-2 ring-red-400/50" : "bg-emerald-400"
              }`}
              style={{ left: `${b.x}%`, top: `${b.y}%` }}
            />
          ))}
        </div>

        <div className="bg-slate-900 border border-slate-700 rounded-xl p-4">
          <h2 className="text-white font-medium mb-3">Active BOPs</h2>
          {filtered.length === 0 ? (
            <p className="text-slate-500 text-sm">No data</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
              {filtered
                .sort((a, b) => b.count - a.count)
                .map((b) => (
                  <div
                    key={b.bop}
                    className="flex items-center justify-between bg-slate-800 rounded-lg px-3 py-2 border border-slate-700"
                  >
                    <div>
                      <p className="text-white text-sm font-medium">{b.bop}</p>
                      <p className="text-slate-500 text-xs">{b.sector} Frontier</p>
                    </div>
                    <div className="text-right">
                      <p className="text-slate-300 text-sm">{b.count} alerts</p>
                      {b.high > 0 && <p className="text-red-400 text-xs">{b.high} HIGH</p>}
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
