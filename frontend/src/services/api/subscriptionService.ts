import { Subscription, SubscriptionStatus, IpAddress } from '../../types/subscription';

// Mock data for development
const API_BASE_URL = '/api/v1';

const mockSubscription: Subscription = {
  id: 'sub_123',
  user_id: 'user_123',
  node_id: 'node_123',
  plan_id: 'plan_pro',
  status: 'active',
  traffic_used: 1073741824, // 1 GB in bytes
  traffic_limit: 10737418240, // 10 GB in bytes
  ip_restriction: 'enabled',
  ip_whitelist: [
    { id: 'ip1', ip: '192.168.1.1', created_at: '2023-05-15T10:30:00Z', created_by: 'admin' },
    { id: 'ip2', ip: '10.0.0.0/24', created_at: '2023-05-16T14:45:00Z', created_by: 'admin' },
  ],
  ip_blacklist: [
    { id: 'ip3', ip: '185.143.223.10', created_at: '2023-05-17T09:15:00Z', created_by: 'admin', notes: 'Suspicious activity' },
  ],
  created_at: '2023-05-01T00:00:00Z',
  updated_at: '2023-05-20T15:30:00Z',
  expires_at: '2023-06-01T00:00:00Z',
  last_connected_at: '2023-05-20T14:30:00Z',
  last_ip: '192.168.1.1',
  is_active: true,
  notes: 'VIP client',
  metadata: {
    protocol: 'wireguard',
    config: {
      private_key: 'mNtHqK1RfUvXcZxBnMlKjHpLpOoIuYtFg',
      public_key: 'hUvXcZxBnMlKjHpLpOoIuYtFgRtYtFv',
      address: '10.8.0.2/24',
      dns: '1.1.1.1, 8.8.8.8',
      endpoint: 'vpn.example.com:51820',
      allowed_ips: '0.0.0.0/0, ::/0',
      persistent_keepalive: 25,
    },
  },
};

export const subscriptionService = {
  async getSubscription(id: string): Promise<Subscription> {
    // In a real app, this would be an API call
    return new Promise((resolve) => {
      setTimeout(() => resolve(mockSubscription), 500);
    });
  },

  async updateSubscription(id: string, data: Partial<Subscription>): Promise<Subscription> {
    // In a real app, this would be an API call
    return new Promise((resolve) => {
      setTimeout(() => {
        const updated = { ...mockSubscription, ...data, id };
        Object.assign(mockSubscription, updated);
        resolve(updated);
      }, 500);
    });
  },

  async deleteSubscription(id: string): Promise<void> {
    // In a real app, this would be an API call
    return new Promise((resolve) => {
      setTimeout(() => resolve(), 500);
    });
  },

  async updateSubscriptionStatus(id: string, status: SubscriptionStatus): Promise<Subscription> {
    return this.updateSubscription(id, { status });
  },

  async updateSubscriptionIpWhitelist(id: string, ips: string[]): Promise<Subscription> {
    const whitelist = ips.map(ip => ({
      id: `ip_${Date.now()}_${Math.floor(Math.random() * 1000)}`,
      ip,
      created_at: new Date().toISOString(),
      created_by: 'current_user', // This would be the actual user ID in a real app
    }));
    
    return this.updateSubscription(id, { ip_whitelist: whitelist });
  },

  async updateSubscriptionIpBlacklist(id: string, ips: string[]): Promise<Subscription> {
    const blacklist = ips.map(ip => ({
      id: `ip_${Date.now()}_${Math.floor(Math.random() * 1000)}`,
      ip,
      created_at: new Date().toISOString(),
      created_by: 'current_user', // This would be the actual user ID in a real app
      notes: 'Added via UI',
    }));
    
    return this.updateSubscription(id, { ip_blacklist: blacklist });
  },

  async getSubscriptionUsage(id: string, startDate: Date, endDate: Date) {
    // In a real app, this would be an API call
    return new Promise((resolve) => {
      setTimeout(() => {
        const days = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
        const usage = {
          daily: Array.from({ length: days }, (_, i) => ({
            date: new Date(startDate.getTime() + i * 24 * 60 * 60 * 1000).toISOString(),
            upload: Math.floor(Math.random() * 1000000000) + 500000000, // 0.5-1.5 GB
            download: Math.floor(Math.random() * 3000000000) + 1000000000, // 1-4 GB
          })),
          hourly: Array.from({ length: 24 }, (_, i) => ({
            hour: i,
            upload: Math.floor(Math.random() * 50000000) + 10000000, // 10-60 MB
            download: Math.floor(Math.random() * 200000000) + 50000000, // 50-250 MB
  })),
        };
        resolve(usage);
      }, 500);
    });
  },

  async getSubscriptionLogs(
    id: string, 
    filters: { 
      search?: string; 
      status?: string; 
      action?: string;
      page?: number;
      limit?: number;
    } = {}
  ) {
    // In a real app, this would be an API call
    return new Promise<{ logs: any[]; total: number }>((resolve) => {
      setTimeout(() => {
        // Generate mock logs
        const logs = Array.from({ length: 100 }, (_, i) => ({
          id: `log_${i + 1}`,
          timestamp: new Date(Date.now() - Math.floor(Math.random() * 7 * 24 * 60 * 60 * 1000)).toISOString(),
          action: ['connect', 'disconnect', 'auth_success', 'auth_failed', 'limit_reached'][Math.floor(Math.random() * 5)],
          ip_address: `192.168.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`,
          user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
          location: {
            country: ['Russia', 'USA', 'Germany', 'China', 'Japan'][Math.floor(Math.random() * 5)],
            city: ['Moscow', 'New York', 'Berlin', 'Beijing', 'Tokyo'][Math.floor(Math.random() * 5)],
            isp: ['Rostelecom', 'MTS', 'Beeline', 'Megafon', 'Yota'][Math.floor(Math.random() * 5)],
          },
          bytes_sent: Math.floor(Math.random() * 100000000) + 1000000, // 1-101 MB
          bytes_received: Math.floor(Math.random() * 500000000) + 100000000, // 100-600 MB
          duration: Math.floor(Math.random() * 3600) + 60, // 1 min - 1 hour
          status: ['success', 'warning', 'error', 'info'][Math.floor(Math.random() * 4)] as 'success' | 'warning' | 'error' | 'info',
          details: Math.random() > 0.7 ? 'Additional error or warning information' : undefined,
        }));

        // Apply filters
        let filteredLogs = [...logs];
        
        if (filters.search) {
          const searchLower = filters.search.toLowerCase();
          filteredLogs = filteredLogs.filter(
            log => 
              log.ip_address.includes(filters.search!) ||
              (log.user_agent && log.user_agent.toLowerCase().includes(searchLower)) ||
              (log.location?.country && log.location.country.toLowerCase().includes(searchLower)) ||
              (log.location?.city && log.location.city.toLowerCase().includes(searchLower)) ||
              (log.location?.isp && log.location.isp.toLowerCase().includes(searchLower))
          );
        }
        
        if (filters.status) {
          filteredLogs = filteredLogs.filter(log => log.status === filters.status);
        }
        
        if (filters.action) {
          filteredLogs = filteredLogs.filter(log => log.action === filters.action);
        }
        
        // Apply pagination
        const page = filters.page || 0;
        const limit = filters.limit || 10;
        const start = page * limit;
        const paginatedLogs = filteredLogs.slice(start, start + limit);
        
        resolve({
          logs: paginatedLogs,
          total: filteredLogs.length,
        });
      }, 500);
    });
  },
};
