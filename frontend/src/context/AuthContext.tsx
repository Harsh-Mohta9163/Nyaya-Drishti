import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiLogin, apiRegister, apiGetMe, clearTokens, getAccessToken } from '../api';

interface User {
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
  const [isLoading, setIsLoading] = useState(true); // Start true to check existing session

  // On mount, check if we have a stored token and validate it
  useEffect(() => {
    const checkSession = async () => {
      const token = getAccessToken();
      if (!token) {
        setIsLoading(false);
        return;
      }
      try {
        const userData = await apiGetMe();
        setUser({
          username: userData.first_name || userData.email?.split('@')[0] || 'User',
          email: userData.email,
          role: userData.role || 'reviewer',
          department: userData.department || 'legal',
        });
      } catch {
        // Token expired or invalid — clear it
        clearTokens();
      } finally {
        setIsLoading(false);
      }
    };
    checkSession();
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const data = await apiLogin(email, password);
      // The apiLogin function already stores tokens
      // Now fetch the user profile
      try {
        const userData = await apiGetMe();
        setUser({
          username: userData.first_name || email.split('@')[0],
          email: userData.email || email,
          role: userData.role || 'reviewer',
          department: userData.department || 'legal',
        });
      } catch {
        // Fallback: use data from login response if /me/ fails
        setUser({
          username: data.user?.first_name || email.split('@')[0],
          email: data.user?.email || email,
          role: data.user?.role || 'reviewer',
          department: data.user?.department || 'legal',
        });
      }
    } catch (err: any) {
      throw err; // Let the login page handle the error display
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: any) => {
    setIsLoading(true);
    try {
      await apiRegister(userData);
      // Don't auto-login after register — user will go to login page
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    clearTokens();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      isAuthenticated: !!user, 
      isLoading, 
      login, 
      register, 
      logout 
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
