import { useEffect, useState } from "react";
import Navbar from "../components/Navbar";

export default function GlobalTracks() {
  const [tracks, setTracks] = useState([]);

  useEffect(() => {
    // Placeholder - will be connected to /fusion/active when available
    setTracks([]);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950">
      <Navbar />
      <div className="p-6 max-w-7xl mx-auto">
        <h1 className="text-white text-2xl font-bold mb-6">Global Multi-Camera Tracks</h1>
        {tracks.length === 0 ? (
          <p className="text-slate-400">No active global tracks. Multi-camera fusion will appear here.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {tracks.map((track) => (
              <div key={track.global_id} className="bg-slate-900 border border-slate-700 rounded-xl p-5">
                <p className="text-white font-semibold">Global ID: {track.global_id}</p>
                <p className="text-slate-400 text-sm mt-1">{track.label}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
