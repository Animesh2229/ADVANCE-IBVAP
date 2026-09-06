import { createContext, useContext, useState, useEffect } from "react";
import api from "../api/axios";

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get("/me");
        setUser(res.data);
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const login = async (username, password) => {
    const params = new URLSearchParams();
    params.append("username", username);
    params.append("password", password);

    const res = await api.post("/auth/login", params, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });

    const userData = {
      username,
      role: res.data.role,
      full_name: res.data.full_name,
      must_change_password: res.data.must_change_password,
    };
    setUser(userData);
    return userData;
  };

  const changePassword = async (current_password, new_password) => {
    await api.post("/auth/change-password", { current_password, new_password });
    setUser((u) => (u ? { ...u, must_change_password: false } : u));
  };

  const logout = async () => {
    try {
      await api.post("/auth/logout");
    } catch (_) {}
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, changePassword }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
