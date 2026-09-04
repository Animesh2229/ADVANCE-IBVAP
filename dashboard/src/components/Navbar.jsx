import { useAuth } from "../context/AuthContext";
import { useNavigate, NavLink } from "react-router-dom";
import { Shield, LogOut } from "lucide-react";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="bg-slate-900 border-b border-slate-700 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <Shield className="text-blue-500" size={24} />
        <span className="text-white font-semibold text-lg">IBVAP Command</span>
      </div>

      <div className="flex items-center gap-5 text-sm">
        <NavLink to="/" className={({isActive}) => isActive ? "text-blue-400" : "text-slate-300 hover:text-white"}>Alerts</NavLink>
        <NavLink to="/watchlist" className={({isActive}) => isActive ? "text-blue-400" : "text-slate-300 hover:text-white"}>Watchlist</NavLink>
        <NavLink to="/global-tracks" className={({isActive}) => isActive ? "text-blue-400" : "text-slate-300 hover:text-white"}>Global Tracks</NavLink>
        <NavLink to="/reports" className={({isActive}) => isActive ? "text-blue-400" : "text-slate-300 hover:text-white"}>Reports</NavLink>
        {user?.role === "admin" && (
          <NavLink to="/users" className={({isActive}) => isActive ? "text-blue-400" : "text-slate-300 hover:text-white"}>Users</NavLink>
        )}

        <div className="text-right ml-4">
          <p className="text-white text-sm font-medium">{user?.full_name}</p>
          <p className="text-slate-400 text-xs capitalize">{user?.role}</p>
        </div>
        <button onClick={handleLogout} className="text-slate-400 hover:text-red-400 transition" title="Logout">
          <LogOut size={20} />
        </button>
      </div>
    </nav>
  );
}
