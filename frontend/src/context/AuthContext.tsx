import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authLogin, authLogout, LoginResponse } from '../api/client';

interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  department: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (userData: any) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Restore user from localStorage on page load (if token exists)
  useEffect(() => {
    const savedUser = localStorage.getItem('user_data');
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch {
        localStorage.removeItem('user_data');
      }
    }
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const data: LoginResponse = await authLogin(email, password);
      setUser(data.user);
      localStorage.setItem('user_data', JSON.stringify(data.user));
    } catch (e: any) {
      setIsLoading(false);
      throw e; // re-throw so LoginPage can show the message
    }
    setIsLoading(false);
  };

  const register = async (userData: any) => {
    setIsLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/auth/register/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData),
      });
      if (!res.ok) {
        const raw = await res.json().catch(() => ({}));
        // DRF returns field errors as { field: ["msg"] } or { detail: "msg" }
        const message = raw?.detail
          || Object.entries(raw)
               .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
               .join(' | ')
          || 'Registration failed';
        throw new Error(message);
      }
      // After registration, user must log in manually
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    authLogout();
    localStorage.removeItem('user_data');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: !!user,
      isLoading,
      login,
      register,
      logout,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
