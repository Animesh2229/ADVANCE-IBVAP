import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useNavigate, NavLink } from "react-router-dom";
import { Shield, LogOut, Globe } from "lucide-react";

export default function Navbar() {
  const { user, logout } = useAuth();
  const { lang, setLang, t, languageNames, available } = useLanguage();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const link = ({ isActive }) => (isActive ? "text-blue-400" : "text-slate-300 hover:text-white");

  return (
    <nav className="bg-slate-900 border-b border-slate-700 px-6 py-3 flex items-center justify-between flex-wrap gap-2">
      <div className="flex items-center gap-3">
        <Shield className="text-blue-500" size={24} />
        <span className="text-white font-semibold text-lg">{t("appName")}</span>
      </div>

      <div className="flex items-center gap-4 text-sm flex-wrap">
        <NavLink to="/" className={link}>{t("dashboard")}</NavLink>
        <NavLink to="/bops" className={link}>{t("bopsMap")}</NavLink>
        <NavLink to="/watchlist" className={link}>{t("watchlist")}</NavLink>
        <NavLink to="/global-tracks" className={link}>{t("globalTracks")}</NavLink>
        <NavLink to="/reports" className={link}>{t("reports")}</NavLink>
        {user?.role === "admin" && (
          <NavLink to="/users" className={link}>{t("users")}</NavLink>
        )}

        <div className="flex items-center gap-1 ml-2">
          <Globe size={16} className="text-slate-400" />
          <select
            value={lang}
            onChange={(e) => setLang(e.target.value)}
            className="bg-slate-800 border border-slate-600 text-white rounded px-2 py-1 text-xs"
            title={t("language")}
          >
            {available.map((code) => (
              <option key={code} value={code}>
                {languageNames[code]}
              </option>
            ))}
          </select>
        </div>

        <div className="text-right ml-2">
          <p className="text-white text-sm font-medium">{user?.full_name}</p>
          <p className="text-slate-400 text-xs capitalize">{user?.role}</p>
        </div>
        <button onClick={handleLogout} className="text-slate-400 hover:text-red-400 transition" title={t("logout")}>
          <LogOut size={20} />
        </button>
      </div>
    </nav>
  );
}
