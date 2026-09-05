import { createContext, useContext, useState, useEffect } from "react";
import api from "../api/axios";

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    const savedUser = localStorage.getItem("user");
    if (token && savedUser) {
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  const login = async (username, password) => {
    // OAuth2PasswordRequestForm expects application/x-www-form-urlencoded
    const params = new URLSearchParams();
    params.append("username", username);
    params.append("password", password);

    const res = await api.post("/auth/login", params, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });

    const { access_token, role, full_name } = res.data;
    const userData = { username, role, full_name };

    localStorage.setItem("token", access_token);
    localStorage.setItem("user", JSON.stringify(userData));
    setUser(userData);
    return userData;
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
