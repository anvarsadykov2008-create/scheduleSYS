import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { apiClient, API_URL } from '../api/client';

interface User {
  id: number;
  username: string;
  role: string;
  full_name: string | null;
  teacher_id: number | null;
  group_id: number | null;
  is_not_student?: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isAdmin: boolean;
  isDispatcher: boolean;
  isTeacher: boolean;
  isStudent: boolean;
  isManagement: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    try {
      const data = await apiClient.get<User>('/auth/users/me');
      setUser(data);
    } catch {
      localStorage.removeItem('token');
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (token) {
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [token, fetchUser]);

  const login = async (username: string, password: string) => {
    const form = new URLSearchParams();
    form.append('username', username);
    form.append('password', password);

    let response;
    try {
      response = await fetch(`${API_URL}/auth/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: form.toString(),
      });
    } catch (err: any) {
      throw new Error(`Ошибка сети (${API_URL}): ${err.message}`);
    }

    if (!response.ok) {
      const errBody = await response.json().catch(() => ({}));
      throw new Error(errBody.detail || 'Неверный ИИН или пароль');
    }

    const data = await response.json();
    localStorage.setItem('token', data.access_token);
    setToken(data.access_token);
    const me = await apiClient.get<User>('/auth/users/me');
    setUser(me);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const role = user?.role ?? '';
  return (
    <AuthContext.Provider value={{
      user, token, loading, login, logout,
      isAdmin: role === 'ADMIN',
      isDispatcher: role === 'DISPATCHER',
      isTeacher: role === 'TEACHER',
      isStudent: role === 'STUDENT',
      isManagement: role === 'MANAGEMENT',
    }}>
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
