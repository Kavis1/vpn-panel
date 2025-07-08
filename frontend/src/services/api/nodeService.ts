import { Node } from '../../types/node';

// Mock data for development
const MOCK_NODE: Node = {
  id: 'node_123',
  name: 'Москва #1',
  hostname: 'vpn-moscow-1.example.com',
  ip_address: '185.143.223.1',
  country: 'Россия',
  city: 'Москва',
  status: 'online',
  is_active: true,
  max_users: 1000,
  current_users: 754,
  load_average: 0.45,
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-05-20T15:00:00Z',
  metadata: {
    location: 'Дата-центр M1',
    provider: 'Cloud Provider Inc.',
    tags: ['premium', 'wireguard'],
  },
};

const getNodeById = async (id: string): Promise<Node> => {
  console.log(`Fetching node with id: ${id}`);
  // In a real app, you would make an API call here.
  return new Promise(resolve => setTimeout(() => resolve(MOCK_NODE), 500));
};

export const nodeService = {
  getNodeById,
};
