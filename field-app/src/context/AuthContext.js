import React, { createContext, useState, useEffect, useContext } from 'react';
import * as SecureStore from 'expo-secure-store';
import api from '../services/api';

const AuthContext = createContext(null);
const TOKEN_KEY = 'ibvap_token';
const USER_KEY = 'ibvap_user';

async function saveSecure(key, value) {
  await SecureStore.setItemAsync(key, value);
}

async function loadSecure(key) {
  return SecureStore.getItemAsync(key);
}

async function deleteSecure(key) {
  try {
    await SecureStore.deleteItemAsync(key);
  } catch (_) {}
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      const token = await loadSecure(TOKEN_KEY);
      const userData = await loadSecure(USER_KEY);
      if (token && userData) {
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        setUser(JSON.parse(userData));
      }
    } catch (e) {
      console.warn('Failed to load user', e);
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    const form = new URLSearchParams();
    form.append('username', username);
    form.append('password', password);
    const res = await api.post('/auth/login', form.toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    const { access_token, role, full_name, must_change_password } = res.data;
    const userObj = { username, role, full_name, must_change_password };
    await saveSecure(TOKEN_KEY, access_token);
    await saveSecure(USER_KEY, JSON.stringify(userObj));
    api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    setUser(userObj);
    return userObj;
  };

  const logout = async () => {
    await deleteSecure(TOKEN_KEY);
    await deleteSecure(USER_KEY);
    delete api.defaults.headers.common['Authorization'];
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
