import { User } from '../../types/user';

const MOCK_USER: User = {
  id: 'user_123',
  username: 'ivanov',
  email: 'ivanov@example.com',
  full_name: 'Иванов Иван Иванович',
  role: 'user',
  status: 'active',
  created_at: '2023-01-15T10:30:00Z',
  last_login_at: '2023-05-20T14:25:00Z',
  metadata: {
    company: 'ООО "Ромашка"',
    phone: '+7 (999) 123-45-67',
  },
};

const getUserById = async (id: string): Promise<User> => {
  console.log(`Fetching user with id: ${id}`);
  // In a real app, you would make an API call here.
  return new Promise(resolve => setTimeout(() => resolve(MOCK_USER), 500));
};

export const userService = {
  getUserById,
};
