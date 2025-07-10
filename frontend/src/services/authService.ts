import axios from 'axios';
import { API_BASE_URL, AUTH_TOKEN_KEY, REFRESH_TOKEN_KEY } from '../config';

interface LoginResponse {
  access_token: string;
  refresh_token?: string;
  user: {
    id: string;
    username: string;
    email: string;
    is_admin: boolean;
  };
}

interface UserProfile {
  id: string;
  username: string;
  email: string;
  is_admin: boolean;
  // Add other user properties as needed
}

// Create axios instance with base URL
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token in requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);
// Add response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // If the error is 401 and we haven't already tried to refresh the token
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
        if (!refreshToken) {
          // No refresh token, redirect to login
          window.location.href = '/login';
          return Promise.reject(error);
        }

        // Try to refresh the token
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, { refresh_token: refreshToken });
        const { access_token, refresh_token } = response.data;

        // Update tokens in storage
        localStorage.setItem(AUTH_TOKEN_KEY, access_token);
        if (refresh_token) {
          localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);
        }
        
        // Update the authorization header
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        
        // Retry the original request
        return api(originalRequest);
      } catch (refreshError) {
        // If refresh fails, clear tokens and redirect to login
        localStorage.removeItem(AUTH_TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export const login = async (username: string, password: string): Promise<LoginResponse> => {
  const response = await api.post('/auth/token', new URLSearchParams({
    username,
    password,
    grant_type: 'password',
  }), {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  return response.data;
};

export const logout = async (): Promise<void> => {
  try {
    await api.post('/auth/logout');
  } catch (error) {
    console.error('Logout error:', error);
  } finally {
    // Clear tokens from storage even if the API call fails
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }
};

export const getCurrentUser = async (): Promise<UserProfile> => {
  const response = await api.get('/auth/me');
  return response.data;
};

export const refreshToken = async (refreshToken: string): Promise<{ access_token: string; refresh_token?: string }> => {
  const response = await api.post('/auth/refresh', { refresh_token: refreshToken });
  return response.data;
};

export const register = async (userData: {
  username: string;
  email: string;
  password: string;
  // Add other registration fields as needed
}) => {
  const response = await api.post('/auth/register', userData);
  return response.data;
};
