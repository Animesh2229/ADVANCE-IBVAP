import React, { createContext, useState, useEffect, useContext } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      const token = await AsyncStorage.getItem('token');
      const userData = await AsyncStorage.getItem('user');
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
    const { access_token, role, full_name } = res.data;
    const userObj = { username, role, full_name };
    await AsyncStorage.setItem('token', access_token);
    await AsyncStorage.setItem('user', JSON.stringify(userObj));
    api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    setUser(userObj);
    return userObj;
  };

  const logout = async () => {
    await AsyncStorage.multiRemove(['token', 'user']);
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
