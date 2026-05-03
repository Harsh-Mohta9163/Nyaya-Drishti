import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import type { User } from '../types';
import { mockUser } from '../lib/mockData';
import { USE_MOCK, mockDelay, api } from '../lib/api';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: { username: string; email: string; password: string; role: string; department?: string }) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const savedUser = localStorage.getItem('user');
    if (token && savedUser) {
      setUser(JSON.parse(savedUser));
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, _password: string) => {
    setIsLoading(true);
    try {
      if (USE_MOCK) {
        await mockDelay(800);
        const u = { ...mockUser, email };
        localStorage.setItem('access_token', 'mock_access_token');
        localStorage.setItem('refresh_token', 'mock_refresh_token');
        localStorage.setItem('user', JSON.stringify(u));
        setUser(u);
      } else {
        const { data } = await api.post('/api/auth/login/', { email, password: _password });
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        localStorage.setItem('user', JSON.stringify(data.user));
        setUser(data.user);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (regData: { username: string; email: string; password: string; role: string; department?: string }) => {
    setIsLoading(true);
    try {
      if (USE_MOCK) {
        await mockDelay(800);
        const u = { ...mockUser, ...regData, id: Date.now() } as User;
        localStorage.setItem('access_token', 'mock_access_token');
        localStorage.setItem('refresh_token', 'mock_refresh_token');
        localStorage.setItem('user', JSON.stringify(u));
        setUser(u);
      } else {
        const { data } = await api.post('/api/auth/register/', regData);
        localStorage.setItem('access_token', data.tokens.access);
        localStorage.setItem('refresh_token', data.tokens.refresh);
        localStorage.setItem('user', JSON.stringify(data.user));
        setUser(data.user);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
