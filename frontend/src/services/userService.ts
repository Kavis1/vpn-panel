import axios from 'axios';
import { API_BASE_URL } from '../config';

// Types
export interface User {
  id: string;
  username: string;
  email: string;
  status: 'active' | 'suspended' | 'expired';
  data_limit?: number;
  data_used?: number;
  expire_date?: string;
  created_at: string;
  updated_at?: string;
  is_admin: boolean;
  last_login?: string;
  subscription_url?: string;
  subscription_id?: string;
  nodes?: Array<{
    id: string;
    name: string;
    is_online: boolean;
  }>;
}

export interface CreateUserData {
  username: string;
  email: string;
  password?: string;
  status?: 'active' | 'suspended' | 'expired';
  data_limit?: number;
  expire_date?: string;
  is_admin?: boolean;
  nodes?: string[];
}

export interface UpdateUserData extends Partial<CreateUserData> {
  id?: string;
  current_password?: string;
  new_password?: string;
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
    const token = localStorage.getItem('vpn_panel_auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Fetches all users
 */
export const getUsers = async (): Promise<{ data: User[] }> => {
  try {
    const response = await api.get('/users');
    return response.data;
  } catch (error) {
    console.error('Error fetching users:', error);
    throw error;
  }
};

/**
 * Fetches a single user by ID
 */
export const getUser = async (userId: string): Promise<{ data: User }> => {
  try {
    const response = await api.get(`/users/${userId}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching user ${userId}:`, error);
    throw error;
  }
};

/**
 * Creates a new user
 */
export const createUser = async (userData: CreateUserData): Promise<{ data: User }> => {
  try {
    const response = await api.post('/users', userData);
    return response.data;
  } catch (error) {
    console.error('Error creating user:', error);
    throw error;
  }
};

/**
 * Updates an existing user
 */
export const updateUser = async ({
  userId,
  userData,
}: {
  userId: string;
  userData: UpdateUserData;
}): Promise<{ data: User }> => {
  try {
    const response = await api.put(`/users/${userId}`, userData);
    return response.data;
  } catch (error) {
    console.error(`Error updating user ${userId}:`, error);
    throw error;
  }
};

/**
 * Deletes a user
 */
export const deleteUser = async (userId: string): Promise<void> => {
  try {
    await api.delete(`/users/${userId}`);
  } catch (error) {
    console.error(`Error deleting user ${userId}:`, error);
    throw error;
  }
};

/**
 * Toggles user status (active/suspended)
 */
export const toggleUserStatus = async ({
  userId,
  status,
}: {
  userId: string;
  status: 'active' | 'suspended';
}): Promise<{ data: User }> => {
  try {
    const response = await api.patch(`/users/${userId}/status`, { status });
    return response.data;
  } catch (error) {
    console.error(`Error toggling status for user ${userId}:`, error);
    throw error;
  }
};

/**
 * Updates the current user's profile
 */
export const updateProfile = async (userData: UpdateUserData): Promise<{ data: User }> => {
  try {
    const response = await api.patch('/users/me', userData);
    return response.data;
  } catch (error) {
    console.error('Error updating profile:', error);
    throw error;
  }
};

/**
 * Changes the current user's password
 */
export const changePassword = async ({
  currentPassword,
  newPassword,
}: {
  currentPassword: string;
  newPassword: string;
}): Promise<void> => {
  try {
    await api.post('/users/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  } catch (error) {
    console.error('Error changing password:', error);
    throw error;
  }
};

/**
 * Resets a user's password (admin only)
 */
export const resetUserPassword = async ({
  userId,
  newPassword,
}: {
  userId: string;
  newPassword: string;
}): Promise<void> => {
  try {
    await api.post(`/users/${userId}/reset-password`, {
      new_password: newPassword,
    });
  } catch (error) {
    console.error(`Error resetting password for user ${userId}:`, error);
    throw error;
  }
};

/**
 * Gets the current user's profile
 */
export const getCurrentUser = async (): Promise<{ data: User }> => {
  try {
    const response = await api.get('/users/me');
    return response.data;
  } catch (error) {
    console.error('Error fetching current user:', error);
    throw error;
  }
};

/**
 * Generates a new subscription URL for a user
 */
export const generateSubscriptionUrl = async (userId: string): Promise<{ url: string }> => {
  try {
    const response = await api.post(`/users/${userId}/subscription`);
    return response.data;
  } catch (error) {
    console.error(`Error generating subscription URL for user ${userId}:`, error);
    throw error;
  }
};

/**
 * Revokes a user's subscription URL
 */
export const revokeSubscriptionUrl = async (userId: string): Promise<void> => {
  try {
    await api.delete(`/users/${userId}/subscription`);
  } catch (error) {
    console.error(`Error revoking subscription URL for user ${userId}:`, error);
    throw error;
  }
};
