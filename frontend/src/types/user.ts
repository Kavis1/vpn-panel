export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: string;
  status: 'active' | 'inactive' | 'suspended';
  created_at: string;
  last_login_at?: string;
  metadata?: {
    company?: string;
    phone?: string;
    [key: string]: any;
  };
}
