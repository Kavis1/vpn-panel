import axios from 'axios';
import { API_BASE_URL } from '../config';

// Types
export type SubscriptionStatus = 'active' | 'suspended' | 'expired';

export interface SubscriptionPlan {
  id: string;
  name: string;
  price: number;
  data_limit: number; // in bytes, 0 = unlimited
  duration_days: number;
  features?: string[];
}

export interface Subscription {
  id: string;
  user_id: string;
  plan_id: string;
  node_id?: string;
  status: SubscriptionStatus;
  data_limit: number; // in bytes, 0 = unlimited
  data_used: number; // in bytes
  expire_date?: string; // ISO date string
  auto_renew: boolean;
  created_at: string;
  updated_at: string;
  notes?: string;
  last_connected?: string;
  ip_whitelist?: string[];
  ip_blacklist?: string[];
}

export interface CreateSubscriptionData {
  user_id: string;
  plan_id: string;
  node_id?: string;
  status?: SubscriptionStatus;
  data_limit?: number;
  data_used?: number;
  expire_date?: string;
  auto_renew?: boolean;
  notes?: string;
}

export interface UpdateSubscriptionData extends Partial<CreateSubscriptionData> {}

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
 * Fetches all subscriptions
 */
export const getSubscriptions = async (): Promise<{ data: Subscription[] }> => {
  try {
    const response = await api.get('/subscriptions');
    return response.data;
  } catch (error) {
    console.error('Error fetching subscriptions:', error);
    throw error;
  }
};

/**
 * Fetches a single subscription by ID
 */
export const getSubscription = async (subscriptionId: string): Promise<{ data: Subscription }> => {
  try {
    const response = await api.get(`/subscriptions/${subscriptionId}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching subscription ${subscriptionId}:`, error);
    throw error;
  }
};

/**
 * Creates a new subscription
 */
export const createSubscription = async (
  subscriptionData: CreateSubscriptionData
): Promise<{ data: Subscription }> => {
  try {
    const response = await api.post('/subscriptions', subscriptionData);
    return response.data;
  } catch (error) {
    console.error('Error creating subscription:', error);
    throw error;
  }
};

/**
 * Updates an existing subscription
 */
export const updateSubscription = async ({
  subscriptionId,
  subscriptionData,
}: {
  subscriptionId: string;
  subscriptionData: UpdateSubscriptionData;
}): Promise<{ data: Subscription }> => {
  try {
    const response = await api.put(`/subscriptions/${subscriptionId}`, subscriptionData);
    return response.data;
  } catch (error) {
    console.error(`Error updating subscription ${subscriptionId}:`, error);
    throw error;
  }
};

/**
 * Deletes a subscription
 */
export const deleteSubscription = async (subscriptionId: string): Promise<void> => {
  try {
    await api.delete(`/subscriptions/${subscriptionId}`);
  } catch (error) {
    console.error(`Error deleting subscription ${subscriptionId}:`, error);
    throw error;
  }
};

/**
 * Renews a subscription by extending its expiration date
 */
export const renewSubscription = async ({
  subscriptionId,
  days,
}: {
  subscriptionId: string;
  days: number;
}): Promise<{ data: Subscription }> => {
  try {
    const response = await api.post(`/subscriptions/${subscriptionId}/renew`, { days });
    return response.data;
  } catch (error) {
    console.error(`Error renewing subscription ${subscriptionId}:`, error);
    throw error;
  }
};

/**
 * Toggles subscription status (active/suspended)
 */
export const toggleSubscriptionStatus = async ({
  subscriptionId,
  status,
}: {
  subscriptionId: string;
  status: 'active' | 'suspended';
}): Promise<{ data: Subscription }> => {
  try {
    const response = await api.patch(`/subscriptions/${subscriptionId}/status`, { status });
    return response.data;
  } catch (error) {
    console.error(`Error toggling status for subscription ${subscriptionId}:`, error);
    throw error;
  }
};

/**
 * Gets subscription usage statistics
 */
export const getSubscriptionUsage = async (
  subscriptionId: string,
  {
    startDate,
    endDate,
    granularity = 'day',
  }: {
    startDate: string;
    endDate: string;
    granularity?: 'hour' | 'day' | 'week' | 'month';
  }
): Promise<{ data: Array<{ date: string; bytes_used: number }> }> => {
  try {
    const response = await api.get(`/subscriptions/${subscriptionId}/usage`, {
      params: { start_date: startDate, end_date: endDate, granularity },
    });
    return response.data;
  } catch (error) {
    console.error(`Error getting usage for subscription ${subscriptionId}:`, error);
    throw error;
  }
};

/**
 * Gets subscription connection logs
 */
export const getSubscriptionLogs = async (
  subscriptionId: string,
  {
    limit = 100,
    offset = 0,
    sort = 'desc',
  }: {
    limit?: number;
    offset?: number;
    sort?: 'asc' | 'desc';
  } = {}
): Promise<{ data: Array<{ timestamp: string; action: string; ip: string; details: any }> }> => {
  try {
    const response = await api.get(`/subscriptions/${subscriptionId}/logs`, {
      params: { limit, offset, sort },
    });
    return response.data;
  } catch (error) {
    console.error(`Error getting logs for subscription ${subscriptionId}:`, error);
    throw error;
  }
};

/**
 * Updates IP whitelist for a subscription
 */
export const updateIpWhitelist = async ({
  subscriptionId,
  ipAddresses,
}: {
  subscriptionId: string;
  ipAddresses: string[];
}): Promise<{ data: Subscription }> => {
  try {
    const response = await api.put(`/subscriptions/${subscriptionId}/ip-whitelist`, {
      ip_addresses: ipAddresses,
    });
    return response.data;
  } catch (error) {
    console.error(`Error updating IP whitelist for subscription ${subscriptionId}:`, error);
    throw error;
  }
};

/**
 * Updates IP blacklist for a subscription
 */
export const updateIpBlacklist = async ({
  subscriptionId,
  ipAddresses,
}: {
  subscriptionId: string;
  ipAddresses: string[];
}): Promise<{ data: Subscription }> => {
  try {
    const response = await api.put(`/subscriptions/${subscriptionId}/ip-blacklist`, {
      ip_addresses: ipAddresses,
    });
    return response.data;
  } catch (error) {
    console.error(`Error updating IP blacklist for subscription ${subscriptionId}:`, error);
    throw error;
  }
};

/**
 * Gets available subscription plans
 */
export const getSubscriptionPlans = async (): Promise<{ data: SubscriptionPlan[] }> => {
  try {
    const response = await api.get('/subscription-plans');
    return response.data;
  } catch (error) {
    console.error('Error fetching subscription plans:', error);
    throw error;
  }
};

/**
 * Gets subscription statistics
 */
export const getSubscriptionStats = async (): Promise<{
  data: {
    total: number;
    active: number;
    expired: number;
    suspended: number;
    total_revenue: number;
    average_session_duration: number;
    top_plans: Array<{ plan_id: string; count: number; revenue: number }>;
  };
}> => {
  try {
    const response = await api.get('/subscriptions/stats');
    return response.data;
  } catch (error) {
    console.error('Error fetching subscription stats:', error);
    throw error;
  }
};
