import { useEffect, useState } from "react";
import api from "../api/axios";
import Navbar from "../components/Navbar";
import { Plus } from "lucide-react";

export default function Watchlist() {
  const [list, setList] = useState([]);
  const [faces, setFaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({
    plate_number: "", country: "IND", vehicle_type: "", owner_name: "", status: "watch", notes: ""
  });

  const fetchAll = async () => {
    try {
      const [v, f] = await Promise.all([
        api.get("/watchlist"),
        api.get("/face-watchlist").catch(() => ({ data: [] })),
      ]);
      setList(v.data || []);
      setFaces(f.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post("/watchlist", form);
      setShowModal(false);
      setForm({ plate_number: "", country: "IND", vehicle_type: "", owner_name: "", status: "watch", notes: "" });
      fetchAll();
    } catch (err) {
      alert(err.response?.data?.detail || "Error");
    }
  };

  return (
    <div className="min-h-screen bg-slate-950">
      <Navbar />
      <div className="p-6 max-w-7xl mx-auto space-y-10">
        <div>
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-white text-2xl font-bold">Vehicle Watchlist</h1>
            <button onClick={() => setShowModal(true)} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg">
              <Plus size={18} /> Add Plate
            </button>
          </div>
          {loading ? (
            <p className="text-slate-400">Loading...</p>
          ) : list.length === 0 ? (
            <p className="text-slate-400">No plates in watchlist</p>
          ) : (
            <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden">
              <table className="w-full text-left">
                <thead className="bg-slate-800 text-slate-300 text-sm">
                  <tr>
                    <th className="p-4">Plate</th>
                    <th className="p-4">Country</th>
                    <th className="p-4">Status</th>
                    <th className="p-4">Owner</th>
                  </tr>
                </thead>
                <tbody>
                  {list.map((item) => (
                    <tr key={item.id || item.plate_number} className="border-t border-slate-700">
                      <td className="p-4 text-white font-medium">{item.plate_number}</td>
                      <td className="p-4 text-slate-300">{item.country}</td>
                      <td className="p-4 text-slate-300 capitalize">{item.status}</td>
                      <td className="p-4 text-slate-300">{item.owner_name || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div>
          <h2 className="text-white text-xl font-semibold mb-4">Face Watchlist</h2>
          <p className="text-slate-500 text-sm mb-3">
            Enrolled faces for match API (POST /api/v1/face-watchlist/match).
          </p>
          {faces.length === 0 ? (
            <p className="text-slate-400">No face enrollments yet</p>
          ) : (
            <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden">
              <table className="w-full text-left">
                <thead className="bg-slate-800 text-slate-300 text-sm">
                  <tr>
                    <th className="p-4">ID</th>
                    <th className="p-4">Name</th>
                    <th className="p-4">Source camera</th>
                    <th className="p-4">Enrolled</th>
                  </tr>
                </thead>
                <tbody>
                  {faces.map((f) => (
                    <tr key={f.id} className="border-t border-slate-700">
                      <td className="p-4 text-slate-300">{f.id}</td>
                      <td className="p-4 text-white font-medium">{f.person_name}</td>
                      <td className="p-4 text-slate-300">{f.camera_id || "—"}</td>
                      <td className="p-4 text-slate-400 text-sm">
                        {f.timestamp ? new Date(f.timestamp).toLocaleString() : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <form onSubmit={handleSubmit} className="bg-slate-900 border border-slate-700 rounded-xl p-6 w-full max-w-md space-y-3">
            <h3 className="text-white font-semibold text-lg">Add vehicle</h3>
            <input className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white" placeholder="Plate" value={form.plate_number} onChange={(e) => setForm({ ...form, plate_number: e.target.value })} required />
            <input className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white" placeholder="Country" value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })} />
            <input className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white" placeholder="Owner" value={form.owner_name} onChange={(e) => setForm({ ...form, owner_name: e.target.value })} />
            <div className="flex gap-2 justify-end pt-2">
              <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 text-slate-300">Cancel</button>
              <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg">Save</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
