export interface Node {
  id: string;
  name: string;
  hostname: string;
  ip_address: string;
  country: string;
  city: string;
  status: 'online' | 'offline' | 'maintenance';
  is_active: boolean;
  max_users: number;
  current_users: number;
  load_average: number;
  created_at: string;
  updated_at: string;
  metadata?: {
    location?: string;
    provider?: string;
    tags?: string[];
    [key: string]: any;
  };
}
