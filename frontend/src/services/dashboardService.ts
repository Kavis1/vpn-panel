import axios from 'axios';
import { API_BASE_URL, AUTH_TOKEN_KEY } from '../config';

interface DashboardStats {
  total_users: number;
  active_users: number;
  total_traffic_gb: number;
  active_nodes: number;
  total_nodes: number;
  uptime_days: number;
  recent_activities: Array<{
    id: number;
    user: string;
    action: string;
    time: string;
    status: 'success' | 'error' | 'info';
  }>;
  traffic_data?: Array<{
    date: string;
    gb: number;
  }>;
  node_status?: Array<{
    id: number;
    name: string;
    status: 'online' | 'offline' | 'maintenance';
    load: number;
    users: number;
  }>;
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

/**
 * Fetches dashboard statistics
 */
export const getDashboardStats = async (): Promise<DashboardStats> => {
  try {
    const response = await api.get('/dashboard/stats');
    return response.data.data;
  } catch (error) {
    console.error('Error fetching dashboard stats:', error);
    throw error;
  }
};

/**
 * Fetches node status information
 */
export const getNodeStatus = async () => {
  try {
    const response = await api.get('/dashboard/nodes/status');
    return response.data.data;
  } catch (error) {
    console.error('Error fetching node status:', error);
    throw error;
  }
};

/**
 * Fetches recent activity
 */
export const getRecentActivity = async () => {
  try {
    const response = await api.get('/dashboard/recent-activity');
    return response.data.data;
  } catch (error) {
    console.error('Error fetching recent activity:', error);
    throw error;
  }
};

/**
 * Fetches traffic data for the specified time range
 */
export const getTrafficData = async (range: 'day' | 'week' | 'month' = 'week') => {
  try {
    const response = await api.get(`/dashboard/traffic?range=${range}`);
    return response.data.data;
  } catch (error) {
    console.error('Error fetching traffic data:', error);
    throw error;
  }
};

/**
 * Fetches system health information
 */
export const getSystemHealth = async () => {
  try {
    const response = await api.get('/dashboard/health');
    return response.data.data;
  } catch (error) {
    console.error('Error fetching system health:', error);
    throw error;
  }
};
