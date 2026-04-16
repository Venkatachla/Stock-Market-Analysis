/**
 * FIXED Auth Context - Using corrected API calls with proper CORS headers
 * Location: frontend/src/contexts/AuthContext_Fixed.tsx
 */

import React, { createContext, useState, useEffect } from 'react';
import * as api from '../services/api_fixed';

export interface AuthUser {
  id: number;
  email: string;
  name: string;
  tier: string;
  is_admin: boolean;
}

export interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  signup: (email: string, password: string, name: string) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load token from localStorage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem('auth_token');
    const savedUser = localStorage.getItem('auth_user');

    if (savedToken && savedUser) {
      try {
        setToken(savedToken);
        setUser(JSON.parse(savedUser));
        console.log('✅ Loaded auth from localStorage');
      } catch (error) {
        console.error('❌ Error loading auth:', error);
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
      }
    }

    setIsLoading(false);
  }, []);

  const signup = async (email: string, password: string, name: string) => {
    setIsLoading(true);
    try {
      console.log('📝 Starting signup...');
      const response = await api.signup(email, password, name);

      console.log('✅ Signup successful:', response);

      setToken(response.token);
      setUser({
        id: response.user_id,
        email: response.email,
        name: response.name,
        tier: response.tier,
        is_admin: response.is_admin,
      });

      // Save to localStorage
      localStorage.setItem('auth_token', response.token);
      localStorage.setItem('auth_user', JSON.stringify({
        id: response.user_id,
        email: response.email,
        name: response.name,
        tier: response.tier,
        is_admin: response.is_admin,
      }));

      console.log('✅ Auth state updated and saved to localStorage');
    } catch (error) {
      console.error('❌ Signup failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      console.log('🔐 Starting login...');
      const response = await api.login(email, password);

      console.log('✅ Login successful:', response);

      setToken(response.token);
      setUser({
        id: response.user_id,
        email: response.email,
        name: response.name,
        tier: response.tier,
        is_admin: response.is_admin,
      });

      // Save to localStorage
      localStorage.setItem('auth_token', response.token);
      localStorage.setItem('auth_user', JSON.stringify({
        id: response.user_id,
        email: response.email,
        name: response.name,
        tier: response.tier,
        is_admin: response.is_admin,
      }));

      console.log('✅ Auth state updated and saved to localStorage');
    } catch (error) {
      console.error('❌ Login failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    console.log('🚪 Logging out...');
    setUser(null);
    setToken(null);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    console.log('✅ Logged out and cleared localStorage');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        isLoading,
        signup,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
