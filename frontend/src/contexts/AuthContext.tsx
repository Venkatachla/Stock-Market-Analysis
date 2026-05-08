import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { setAuthToken } from '@/services/api';

export interface User {
  email: string;
  tier: string;
  isAdmin?: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ErrorResponse {
  detail?: string;
  message?: string;
}

const sanitizeErrorMessage = (message: string, fallback: string): string => {
  const normalized = message.replace(/\s+/g, ' ').trim();
  if (!normalized) return fallback;

  const lowered = normalized.toLowerCase();
  const sensitiveMarkers = ['traceback', 'exception', 'stack', '/home/', 'line '];
  if (sensitiveMarkers.some((marker) => lowered.includes(marker))) {
    return fallback;
  }

  return normalized.length > 160 ? `${normalized.slice(0, 157)}...` : normalized;
};

const extractErrorMessage = async (response: Response, fallback: string): Promise<string> => {
  const body = await response.text();
  if (!body) return fallback;

  try {
    const parsed = JSON.parse(body) as ErrorResponse;
    const candidate = parsed.detail || parsed.message;
    return candidate ? sanitizeErrorMessage(candidate, fallback) : fallback;
  } catch {
    return fallback;
  }
};

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize from localStorage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem('auth_token');
    const savedUser = localStorage.getItem('auth_user');
    
    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
      setAuthToken(savedToken);
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    const response = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      throw new Error(await extractErrorMessage(response, 'Login failed'));
    }

    const data = await response.json();
    const authToken = data.token;
    const userData: User = {
      email,
      tier: data.tier || 'free',
      isAdmin: data.is_admin || false,
    };

    setToken(authToken);
    setUser(userData);
    setAuthToken(authToken);
    
    localStorage.setItem('auth_token', authToken);
    localStorage.setItem('auth_user', JSON.stringify(userData));
  };

  const signup = async (email: string, password: string) => {
    const response = await fetch(`${API_BASE}/api/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, name: email.split('@')[0] }),
    });

    if (!response.ok) {
      throw new Error(await extractErrorMessage(response, 'Signup failed'));
    }

    const data = await response.json();
    const authToken = data.token;
    const userData: User = {
      email,
      tier: data.tier || 'free',
      isAdmin: data.is_admin || false,
    };

    setToken(authToken);
    setUser(userData);
    setAuthToken(authToken);
    
    localStorage.setItem('auth_token', authToken);
    localStorage.setItem('auth_user', JSON.stringify(userData));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    setAuthToken(null);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        isLoading,
        login,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
