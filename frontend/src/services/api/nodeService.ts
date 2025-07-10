import axios from 'axios';
import { Node } from '../../types/node';
import { API_BASE_URL, AUTH_TOKEN_KEY } from '../../config';

// Types for API requests
export interface CreateNodeData {
  name: string;
  fqdn: string;
  ip_address: string;
  country_code?: string;
  city?: string;
  ssh_host?: string;
  ssh_port?: number;
  ssh_username?: string;
  ssh_password?: string;
  ssh_private_key?: string;
  api_port?: number;
  api_ssl?: boolean;
  api_secret?: string;
  max_users?: number;
  tags?: string[];
  config?: Record<string, any>;
}

export interface UpdateNodeData extends Partial<CreateNodeData> {
  is_active?: boolean;
  is_blocked?: boolean;
}

export interface NodeStats {
  cpu_usage: number;
  ram_usage: number;
  disk_usage: number;
  user_count: number;
  traffic_stats: {
    upload: number;
    download: number;
  };
  uptime: number;
  last_seen: string;
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

export const nodeService = {
  /**
   * Get node by ID
   */
  async getNodeById(id: string): Promise<Node> {
    try {
      const response = await api.get(`/nodes/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching node ${id}:`, error);
      throw error;
    }
  },

  /**
   * Get all nodes
   */
  async getAllNodes(): Promise<Node[]> {
    try {
      const response = await api.get('/nodes');
      return response.data;
    } catch (error) {
      console.error('Error fetching nodes:', error);
      throw error;
    }
  },

  /**
   * Create new node
   */
  async createNode(nodeData: CreateNodeData): Promise<Node> {
    try {
      const response = await api.post('/nodes', nodeData);
      return response.data;
    } catch (error) {
      console.error('Error creating node:', error);
      throw error;
    }
  },

  /**
   * Update existing node
   */
  async updateNode(id: string, nodeData: UpdateNodeData): Promise<Node> {
    try {
      const response = await api.put(`/nodes/${id}`, nodeData);
      return response.data;
    } catch (error) {
      console.error(`Error updating node ${id}:`, error);
      throw error;
    }
  },

  /**
   * Delete node
   */
  async deleteNode(id: string): Promise<void> {
    try {
      await api.delete(`/nodes/${id}`);
    } catch (error) {
      console.error(`Error deleting node ${id}:`, error);
      throw error;
    }
  },

  /**
   * Get node statistics
   */
  async getNodeStats(id: string): Promise<NodeStats> {
    try {
      const response = await api.get(`/nodes/${id}/stats`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching node stats for ${id}:`, error);
      throw error;
    }
  },

  /**
   * Test node connection
   */
  async testNodeConnection(id: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await api.post(`/nodes/${id}/test`);
      return response.data;
    } catch (error) {
      console.error(`Error testing node connection for ${id}:`, error);
      throw error;
    }
  },

  /**
   * Restart node services
   */
  async restartNode(id: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await api.post(`/nodes/${id}/restart`);
      return response.data;
    } catch (error) {
      console.error(`Error restarting node ${id}:`, error);
      throw error;
    }
  },

  /**
   * Get node logs
   */
  async getNodeLogs(id: string, limit: number = 100): Promise<any[]> {
    try {
      const response = await api.get(`/nodes/${id}/logs`, {
        params: { limit }
      });
      return response.data;
    } catch (error) {
      console.error(`Error fetching node logs for ${id}:`, error);
      throw error;
    }
  }
};
