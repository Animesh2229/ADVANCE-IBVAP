import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { Shield, Globe } from "lucide-react";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [mustChange, setMustChange] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, changePassword } = useAuth();
  const { lang, setLang, t, languageNames, available } = useLanguage();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mustChange) {
        await changePassword(password, newPassword);
        navigate("/");
        return;
      }
      const user = await login(username, password);
      if (user.must_change_password) {
        setMustChange(true);
        setPassword("");
      } else {
        navigate("/");
      }
    } catch (err) {
      setError(err.response?.data?.detail || t("invalidCredentials"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl p-8 w-full max-w-md shadow-2xl">
        <div className="flex justify-end mb-2">
          <div className="flex items-center gap-1">
            <Globe size={14} className="text-slate-400" />
            <select
              value={lang}
              onChange={(e) => setLang(e.target.value)}
              className="bg-slate-800 border border-slate-600 text-white rounded px-2 py-1 text-xs"
            >
              {available.map((code) => (
                <option key={code} value={code}>{languageNames[code]}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex flex-col items-center mb-8">
          <div className="bg-blue-600 p-3 rounded-full mb-4">
            <Shield size={32} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">IBVAP</h1>
          <p className="text-slate-400 text-sm mt-1 text-center">{t("appName")}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {!mustChange && (
            <div>
              <label className="block text-sm text-slate-300 mb-1">{t("username")}</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          )}
          <div>
            <label className="block text-sm text-slate-300 mb-1">
              {mustChange ? t("currentPassword") : t("password")}
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          {mustChange && (
            <div>
              <label className="block text-sm text-slate-300 mb-1">{t("newPassword")}</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                minLength={8}
                required
              />
            </div>
          )}
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-2.5 rounded-lg transition disabled:opacity-50"
          >
            {loading ? "…" : mustChange ? t("changePassword") : t("submit")}
          </button>
        </form>
      </div>
    </div>
  );
}
