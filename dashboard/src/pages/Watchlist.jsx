import { useEffect, useState } from "react";
import api from "../api/axios";
import Navbar from "../components/Navbar";
import { Plus, Trash2 } from "lucide-react";

export default function Watchlist() {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({
    plate_number: "", country: "IND", vehicle_type: "", owner_name: "", status: "watch", notes: ""
  });

  const fetchList = async () => {
    try {
      const res = await api.get("/watchlist");
      setList(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchList(); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post("/watchlist", form);
      setShowModal(false);
      setForm({ plate_number: "", country: "IND", vehicle_type: "", owner_name: "", status: "watch", notes: "" });
      fetchList();
    } catch (err) {
      alert(err.response?.data?.detail || "Error");
    }
  };

  return (
    <div className="min-h-screen bg-slate-950">
      <Navbar />
      <div className="p-6 max-w-7xl mx-auto">
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

      {showModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 w-full max-w-md">
            <h2 className="text-white text-lg font-semibold mb-4">Add to Watchlist</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <input required placeholder="Plate Number" value={form.plate_number}
                onChange={(e) => setForm({...form, plate_number: e.target.value.toUpperCase()})}
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-white" />
              <select value={form.country} onChange={(e) => setForm({...form, country: e.target.value})}
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-white">
                <option value="IND">India</option>
                <option value="NPL">Nepal</option>
                <option value="BTN">Bhutan</option>
              </select>
              <input placeholder="Owner Name" value={form.owner_name}
                onChange={(e) => setForm({...form, owner_name: e.target.value})}
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-white" />
              <div className="flex gap-3 pt-2">
                <button type="submit" className="flex-1 bg-blue-600 text-white py-2 rounded-lg">Add</button>
                <button type="button" onClick={() => setShowModal(false)} className="flex-1 bg-slate-700 text-white py-2 rounded-lg">Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
