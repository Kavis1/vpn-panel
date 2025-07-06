import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { login as apiLogin, logout as apiLogout, getCurrentUser } from '../services/authService';
import { AUTH_TOKEN_KEY, REFRESH_TOKEN_KEY } from '../config';

interface User {
  id: string;
  username: string;
  email: string;
  is_admin: boolean;
  // Add other user properties as needed
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  // Check if user is already logged in on initial load
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem(AUTH_TOKEN_KEY);
      if (token) {
        try {
          const userData = await getCurrentUser();
          setUser(userData);
        } catch (error) {
          console.error('Failed to fetch user data', error);
          localStorage.removeItem(AUTH_TOKEN_KEY);
          localStorage.removeItem(REFRESH_TOKEN_KEY);
        }
      }
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (username: string, password: string) => {
    try {
      const { access_token, refresh_token, user: userData } = await apiLogin(username, password);
      
      localStorage.setItem(AUTH_TOKEN_KEY, access_token);
      if (refresh_token) {
        localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);
      }
      
      setUser(userData);
      navigate('/dashboard');
    } catch (error) {
      console.error('Login failed', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await apiLogout();
    } catch (error) {
      console.error('Logout failed', error);
    } finally {
      // Clear auth state regardless of API call result
      localStorage.removeItem(AUTH_TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      setUser(null);
      queryClient.clear();
      navigate('/login');
    }
  };

  const refreshUser = async () => {
    try {
      const userData = await getCurrentUser();
      setUser(userData);
      return userData;
    } catch (error) {
      console.error('Failed to refresh user data', error);
      await logout();
      throw error;
    }
  };

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
