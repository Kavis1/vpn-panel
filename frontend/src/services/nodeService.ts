import axios from 'axios';
import { API_BASE_URL } from '../config';

// Types
export type NodeStatus = 'online' | 'offline' | 'maintenance';

export interface Node {
  id: string;
  name: string;
  host: string;
  port: number;
  api_port: number;
  api_secret: string;
  location: string;
  country: string;
  status: NodeStatus;
  is_active: boolean;
  is_public: boolean;
  max_users: number;
  current_users?: number;
  tags: string[];
  created_at: string;
  updated_at: string;
  last_seen?: string;
  version?: string;
}

export interface NodeStats {
  cpu_percent: number;
  memory_used: number;
  memory_total: number;
  disk_used: number;
  disk_total: number;
  network_rx: number;
  network_tx: number;
  total_network_rx: number;
  total_network_tx: number;
  total_traffic: number;
  uptime: number;
  load_average: number[];
  active_connections: number;
}

export interface NodeConnection {
  id: string;
  user_id: string;
  username: string;
  ip: string;
  protocol: string;
  upload: number;
  download: number;
  connected_at: string;
  connected_time: number; // in seconds
  node_id: string;
}

export interface CreateNodeData {
  name: string;
  host: string;
  port: number;
  api_port: number;
  api_secret: string;
  location?: string;
  country?: string;
  is_active?: boolean;
  is_public?: boolean;
  max_users?: number;
  tags?: string[];
}

export interface UpdateNodeData extends Partial<CreateNodeData> {}

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
 * Fetches all nodes
 */
export const getNodes = async (): Promise<{ data: Node[] }> => {
  try {
    const response = await api.get('/nodes');
    return response.data;
  } catch (error) {
    console.error('Error fetching nodes:', error);
    throw error;
  }
};

/**
 * Fetches a single node by ID
 */
export const getNode = async (nodeId: string): Promise<{ data: Node }> => {
  try {
    const response = await api.get(`/nodes/${nodeId}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching node ${nodeId}:`, error);
    throw error;
  }
};

/**
 * Creates a new node
 */
export const createNode = async (nodeData: CreateNodeData): Promise<{ data: Node }> => {
  try {
    const response = await api.post('/nodes', nodeData);
    return response.data;
  } catch (error) {
    console.error('Error creating node:', error);
    throw error;
  }
};

/**
 * Updates an existing node
 */
export const updateNode = async (
  nodeId: string, 
  nodeData: UpdateNodeData
): Promise<{ data: Node }> => {
  try {
    const response = await api.put(`/nodes/${nodeId}`, nodeData);
    return response.data;
  } catch (error) {
    console.error(`Error updating node ${nodeId}:`, error);
    throw error;
  }
};

/**
 * Deletes a node
 */
export const deleteNode = async (nodeId: string): Promise<void> => {
  try {
    await api.delete(`/nodes/${nodeId}`);
  } catch (error) {
    console.error(`Error deleting node ${nodeId}:`, error);
    throw error;
  }
};

/**
 * Toggles node status (online/offline/maintenance)
 */
export const toggleNodeStatus = async (
  nodeId: string, 
  status: NodeStatus
): Promise<{ data: Node }> => {
  try {
    const response = await api.patch(`/nodes/${nodeId}/status`, { status });
    return response.data;
  } catch (error) {
    console.error(`Error toggling status for node ${nodeId}:`, error);
    throw error;
  }
};

/**
 * Fetches node statistics
 */
export const getNodeStats = async (nodeId: string): Promise<{ data: NodeStats }> => {
  try {
    const response = await api.get(`/nodes/${nodeId}/stats`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching stats for node ${nodeId}:`, error);
    throw error;
  }
};

/**
 * Fetches active connections for a node
 */
export const getNodeConnections = async (nodeId: string): Promise<{ data: NodeConnection[] }> => {
  try {
    const response = await api.get(`/nodes/${nodeId}/connections`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching connections for node ${nodeId}:`, error);
    throw error;
  }
};

/**
 * Tests connection to a node
 */
export const testNodeConnection = async (nodeId: string): Promise<{ success: boolean; message: string }> => {
  try {
    const response = await api.post(`/nodes/${nodeId}/test`);
    return response.data;
  } catch (error) {
    console.error(`Error testing connection to node ${nodeId}:`, error);
    throw error;
  }
};

/**
 * Restarts a node
 */
export const restartNode = async (nodeId: string): Promise<{ success: boolean; message: string }> => {
  try {
    const response = await api.post(`/nodes/${nodeId}/restart`);
    return response.data;
  } catch (error) {
    console.error(`Error restarting node ${nodeId}:`, error);
    throw error;
  }
};

/**
 * Updates node software
 */
export const updateNodeSoftware = async (nodeId: string): Promise<{ success: boolean; message: string }> => {
  try {
    const response = await api.post(`/nodes/${nodeId}/update`);
    return response.data;
  } catch (error) {
    console.error(`Error updating node ${nodeId} software:`, error);
    throw error;
  }
};

/**
 * Gets node logs
 */
export const getNodeLogs = async (
  nodeId: string, 
  limit: number = 100,
  level: 'info' | 'warning' | 'error' | 'debug' = 'info'
): Promise<{ data: string[] }> => {
  try {
    const response = await api.get(`/nodes/${nodeId}/logs`, {
      params: { limit, level }
    });
    return response.data;
  } catch (error) {
    console.error(`Error fetching logs for node ${nodeId}:`, error);
    throw error;
  }
};
