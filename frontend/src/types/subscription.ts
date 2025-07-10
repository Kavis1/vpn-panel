export interface IpAddress {
  id: string;
  ip: string;
  created_at: string;
  created_by: string;
  notes?: string;
}

export type SubscriptionStatus = 'active' | 'suspended' | 'expired' | 'pending';

export interface Subscription {
  id: string;
  user_id: string;
  node_id: string;
  plan_id: string;
  status: SubscriptionStatus;
  traffic_used: number;
  traffic_limit: number;
  ip_restriction: 'enabled' | 'disabled';
  ip_whitelist: IpAddress[];
  ip_blacklist: IpAddress[];
  created_at: string;
  updated_at: string;
  expires_at: string;
  last_connected_at?: string;
  last_ip?: string;
  is_active: boolean;
  notes?: string;
  metadata?: {
    protocol?: string;
    config?: {
      private_key?: string;
      public_key?: string;
      address?: string;
      dns?: string;
      endpoint?: string;
      allowed_ips?: string;
      persistent_keepalive?: number;
      [key: string]: any;
    };
    [key: string]: any;
  };
}

export interface LogEntry {
  id: string;
  timestamp: string;
  action: string;
  ip_address: string;
  user_agent?: string;
  location?: {
    country?: string;
    city?: string;
    isp?: string;
  };
  bytes_sent?: number;
  bytes_received?: number;
  duration?: number;
  status: 'success' | 'warning' | 'error' | 'info';
  details?: string;
}

export interface UsageData {
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
