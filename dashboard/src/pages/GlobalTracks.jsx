import { useEffect, useState } from "react";
import api from "../api/axios";
import Navbar from "../components/Navbar";

export default function GlobalTracks() {
  const [tracks, setTracks] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchTracks = async () => {
    try {
      const res = await api.get("/fusion/active");
      const data = res.data || {};
      setTracks(Object.values(data));
    } catch (err) {
      // Endpoint may not be fully live yet
      setTracks([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTracks();
    const interval = setInterval(fetchTracks, 8000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950">
      <Navbar />
      <div className="p-6 max-w-7xl mx-auto">
        <h1 className="text-white text-2xl font-bold mb-6">Global Multi-Camera Tracks</h1>

        {loading ? (
          <p className="text-slate-400">Loading...</p>
        ) : tracks.length === 0 ? (
          <p className="text-slate-400">No active global tracks right now.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {tracks.map((track) => (
              <div key={track.global_id} className="bg-slate-900 border border-slate-700 rounded-xl p-5">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-white font-semibold">ID: {track.global_id}</p>
                    <p className="text-slate-400 text-sm mt-1 capitalize">{track.label}</p>
                  </div>
                  <span className="text-xs bg-blue-900 text-blue-300 px-2 py-1 rounded">Active</span>
                </div>
                <div className="mt-4 space-y-1 text-sm">
                  <p className="text-slate-300">
                    <span className="text-slate-500">Cameras: </span>
                    {track.cameras?.join(", ") || "—"}
                  </p>
                  <p className="text-slate-300">
                    <span className="text-slate-500">Plates: </span>
                    {track.plates?.length > 0 ? track.plates.join(", ") : "—"}
                  </p>
                  <p className="text-slate-500 text-xs mt-2">
                    Last seen: {track.last_seen ? new Date(track.last_seen).toLocaleString() : "—"}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
