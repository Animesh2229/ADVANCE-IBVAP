import { useEffect, useState } from "react";
import api from "../api/axios";
import Navbar from "../components/Navbar";
import { Plus, Shield } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Users() {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({
    username: "", email: "", password: "", full_name: "", role: "operator"
  });

  const fetchUsers = async () => {
    try {
      const res = await api.get("/users");
      setUsers(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user?.role === "admin") fetchUsers();
  }, [user]);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await api.post("/auth/register", form);
      setShowModal(false);
      setForm({ username: "", email: "", password: "", full_name: "", role: "operator" });
      fetchUsers();
    } catch (err) {
      alert(err.response?.data?.detail || "Error creating user");
    }
  };

  if (user?.role !== "admin") {
    return (
      <div className="min-h-screen bg-slate-950">
        <Navbar />
        <div className="p-10 text-center text-red-400">Access Denied. Admin only.</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950">
      <Navbar />
      <div className="p-6 max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-white text-2xl font-bold flex items-center gap-2">
            <Shield size={24} /> User Management
          </h1>
          <button onClick={() => setShowModal(true)} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg">
            <Plus size={18} /> Add User
          </button>
        </div>

        {loading ? (
          <p className="text-slate-400">Loading...</p>
        ) : (
          <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden">
            <table className="w-full text-left">
              <thead className="bg-slate-800 text-slate-300 text-sm">
                <tr>
                  <th className="p-4">Username</th>
                  <th className="p-4">Full Name</th>
                  <th className="p-4">Role</th>
                  <th className="p-4">Email</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-t border-slate-700">
                    <td className="p-4 text-white">{u.username}</td>
                    <td className="p-4 text-slate-300">{u.full_name}</td>
                    <td className="p-4 text-slate-300 capitalize">{u.role}</td>
                    <td className="p-4 text-slate-300">{u.email}</td>
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
            <h2 className="text-white text-lg font-semibold mb-4">Create New User</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <input required placeholder="Username" value={form.username} onChange={(e) => setForm({...form, username: e.target.value})} className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-white" />
              <input required type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({...form, email: e.target.value})} className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-white" />
              <input required type="password" placeholder="Password" value={form.password} onChange={(e) => setForm({...form, password: e.target.value})} className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-white" />
              <input required placeholder="Full Name" value={form.full_name} onChange={(e) => setForm({...form, full_name: e.target.value})} className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-white" />
              <select value={form.role} onChange={(e) => setForm({...form, role: e.target.value})} className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-white">
                <option value="operator">Operator</option>
                <option value="patroller">Patroller</option>
                <option value="commander">Commander</option>
                <option value="admin">Admin</option>
              </select>
              <div className="flex gap-3">
                <button type="submit" className="flex-1 bg-blue-600 text-white py-2 rounded-lg">Create</button>
                <button type="button" onClick={() => setShowModal(false)} className="flex-1 bg-slate-700 text-white py-2 rounded-lg">Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
