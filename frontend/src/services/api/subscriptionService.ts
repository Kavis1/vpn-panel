import axios from 'axios';
import { Subscription, SubscriptionStatus, IpAddress } from '../../types/subscription';
import { API_BASE_URL, AUTH_TOKEN_KEY } from '../../config';

// Types for API requests
export interface CreateSubscriptionData {
  user_id: string;
  node_id: string;
  plan_id: string;
  expires_at?: string;
  traffic_limit?: number;
  ip_restriction?: 'disabled' | 'enabled';
  notes?: string;
}

export interface UpdateSubscriptionData extends Partial<CreateSubscriptionData> {
  status?: SubscriptionStatus;
  is_active?: boolean;
}

export interface SubscriptionUsageData {
  daily: Array<{
    date: string;
    upload: number;
    download: number;
  }>;
  hourly: Array<{
    hour: number;
    upload: number;
    download: number;
  }>;
}

export interface SubscriptionLogEntry {
  id: string;
  timestamp: string;
  action: string;
  ip_address: string;
  user_agent?: string;
  location?: {
    country: string;
    city: string;
    isp: string;
  };
  bytes_sent: number;
  bytes_received: number;
  duration: number;
  status: 'success' | 'warning' | 'error' | 'info';
  details?: string;
}

export interface SubscriptionLogsResponse {
  logs: SubscriptionLogEntry[];
  total: number;
}

// Create axios instance with base URL and auth
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token
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

export const subscriptionService = {
  /**
   * Get subscription by ID
   */
  async getSubscription(id: string): Promise<Subscription> {
    try {
      const response = await api.get(`/subscriptions/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching subscription ${id}:`, error);
      throw error;
    }
  },

  /**
   * Get all subscriptions
   */
  async getAllSubscriptions(filters?: {
    status?: SubscriptionStatus;
    user_id?: string;
    node_id?: string;
    plan_id?: string;
    page?: number;
    limit?: number;
  }): Promise<{ subscriptions: Subscription[]; total: number }> {
    try {
      const response = await api.get('/subscriptions', { params: filters });
      return response.data;
    } catch (error) {
      console.error('Error fetching subscriptions:', error);
      throw error;
    }
  },

  /**
   * Create new subscription
   */
  async createSubscription(data: CreateSubscriptionData): Promise<Subscription> {
    try {
      const response = await api.post('/subscriptions', data);
      return response.data;
    } catch (error) {
      console.error('Error creating subscription:', error);
      throw error;
    }
  },

  /**
   * Update subscription
   */
  async updateSubscription(id: string, data: UpdateSubscriptionData): Promise<Subscription> {
    try {
      const response = await api.put(`/subscriptions/${id}`, data);
      return response.data;
    } catch (error) {
      console.error(`Error updating subscription ${id}:`, error);
      throw error;
    }
  },

  /**
   * Delete subscription
   */
  async deleteSubscription(id: string): Promise<void> {
    try {
      await api.delete(`/subscriptions/${id}`);
    } catch (error) {
      console.error(`Error deleting subscription ${id}:`, error);
      throw error;
    }
  },

  /**
   * Update subscription status
   */
  async updateSubscriptionStatus(id: string, status: SubscriptionStatus): Promise<Subscription> {
    return this.updateSubscription(id, { status });
  },

  /**
   * Update subscription IP whitelist
   */
  async updateSubscriptionIpWhitelist(id: string, ips: string[]): Promise<Subscription> {
    try {
      const response = await api.put(`/subscriptions/${id}/ip-whitelist`, { ips });
      return response.data;
    } catch (error) {
      console.error(`Error updating IP whitelist for subscription ${id}:`, error);
      throw error;
    }
  },

  /**
   * Update subscription IP blacklist
   */
  async updateSubscriptionIpBlacklist(id: string, ips: string[]): Promise<Subscription> {
    try {
      const response = await api.put(`/subscriptions/${id}/ip-blacklist`, { ips });
      return response.data;
    } catch (error) {
      console.error(`Error updating IP blacklist for subscription ${id}:`, error);
      throw error;
    }
  },

  /**
   * Add IP to whitelist
   */
  async addIpToWhitelist(id: string, ip: string, notes?: string): Promise<Subscription> {
    try {
      const response = await api.post(`/subscriptions/${id}/ip-whitelist`, { ip, notes });
      return response.data;
    } catch (error) {
      console.error(`Error adding IP to whitelist for subscription ${id}:`, error);
      throw error;
    }
  },

  /**
   * Remove IP from whitelist
   */
  async removeIpFromWhitelist(id: string, ipId: string): Promise<Subscription> {
    try {
      const response = await api.delete(`/subscriptions/${id}/ip-whitelist/${ipId}`);
      return response.data;
    } catch (error) {
      console.error(`Error removing IP from whitelist for subscription ${id}:`, error);
      throw error;
    }
  },

  /**
   * Add IP to blacklist
   */
  async addIpToBlacklist(id: string, ip: string, notes?: string): Promise<Subscription> {
    try {
      const response = await api.post(`/subscriptions/${id}/ip-blacklist`, { ip, notes });
      return response.data;
    } catch (error) {
      console.error(`Error adding IP to blacklist for subscription ${id}:`, error);
      throw error;
    }
  },

  /**
   * Remove IP from blacklist
   */
  async removeIpFromBlacklist(id: string, ipId: string): Promise<Subscription> {
    try {
      const response = await api.delete(`/subscriptions/${id}/ip-blacklist/${ipId}`);
      return response.data;
    } catch (error) {
      console.error(`Error removing IP from blacklist for subscription ${id}:`, error);
      throw error;
    }
  },

  /**
   * Get subscription usage statistics
   */
  async getSubscriptionUsage(
    id: string, 
    startDate: Date, 
    endDate: Date
  ): Promise<SubscriptionUsageData> {
    try {
      const response = await api.get(`/subscriptions/${id}/usage`, {
        params: {
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString()
        }
      });
      return response.data;
    } catch (error) {
      console.error(`Error fetching usage for subscription ${id}:`, error);
      throw error;
    }
  },

  /**
   * Get subscription logs
   */
  async getSubscriptionLogs(
    id: string, 
    filters: { 
      search?: string; 
      status?: string; 
      action?: string;
      page?: number;
      limit?: number;
    } = {}
  ): Promise<SubscriptionLogsResponse> {
    try {
      const response = await api.get(`/subscriptions/${id}/logs`, {
        params: filters
      });
      return response.data;
    } catch (error) {
      console.error(`Error fetching logs for subscription ${id}:`, error);
      throw error;
    }
  },

  /**
   * Generate subscription config
   */
  async generateSubscriptionConfig(id: string, format: 'wireguard' | 'openvpn' | 'xray'): Promise<{ config: string }> {
    try {
      const response = await api.post(`/subscriptions/${id}/config`, { format });
      return response.data;
    } catch (error) {
      console.error(`Error generating config for subscription ${id}:`, error);
      throw error;
    }
  },

  /**
   * Reset subscription traffic
   */
  async resetSubscriptionTraffic(id: string): Promise<Subscription> {
    try {
      const response = await api.post(`/subscriptions/${id}/reset-traffic`);
      return response.data;
    } catch (error) {
      console.error(`Error resetting traffic for subscription ${id}:`, error);
      throw error;
    }
  },

  /**
   * Extend subscription
   */
  async extendSubscription(id: string, days: number): Promise<Subscription> {
    try {
      const response = await api.post(`/subscriptions/${id}/extend`, { days });
      return response.data;
    } catch (error) {
      console.error(`Error extending subscription ${id}:`, error);
      throw error;
    }
  }
};
