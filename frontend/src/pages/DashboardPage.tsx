import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Grid,
  Paper,
  Typography,
  CircularProgress,
  useTheme,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
} from '@mui/material';
import {
  People as UsersIcon,
  Dns as NodesIcon,
  Speed as SpeedIcon,
  Storage as StorageIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { getDashboardStats } from '../services/dashboardService';
import Layout from '../components/Layout';

// Types
interface Activity {
  id: number;
  user: string;
  action: string;
  time: string;
  status: 'success' | 'error' | 'info';
}

// Styled components
const StatCard = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  height: '100%',
  borderRadius: (theme.shape.borderRadius as number) * 2,
  transition: 'transform 0.2s, box-shadow 0.2s',
  '&:hover': {
    transform: 'translateY(-4px)',
    boxShadow: theme.shadows[8],
  },
}));

const StatIcon = styled('div')(({ theme, color }) => ({
  width: 60,
  height: 60,
  borderRadius: '50%',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  marginBottom: theme.spacing(2),
  backgroundColor: color ? `${color}15` : theme.palette.primary.light,
  color: color || theme.palette.primary.main,
}));

const StatValue = styled(Typography)(({ theme }) => ({
  fontSize: '2.5rem',
  fontWeight: 'bold',
  margin: theme.spacing(1, 0),
}));

const StatLabel = styled(Typography)(({ theme }) => ({
  color: theme.palette.text.secondary,
  textAlign: 'center',
}));

const DashboardPage: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();

  // Fetch dashboard data
  const { data: stats, isLoading, error, refetch } = useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: getDashboardStats,
    refetchInterval: 60000, // Refresh every minute
  });

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box textAlign="center" p={3}>
        <Typography color="error">
          Ошибка при загрузке данных. Пожалуйста, обновите страницу.
        </Typography>
      </Box>
    );
  }

  // Default values if stats is undefined
  const {
    total_users = 0,
    active_users = 0,
    total_traffic_gb = 0,
    active_nodes = 0,
    total_nodes = 0,
    uptime_days = 0,
  } = stats || {};

  // Calculate percentages
  const activeUsersPercentage = total_users > 0 ? Math.round((active_users / total_users) * 100) : 0;
  const activeNodesPercentage = total_nodes > 0 ? Math.round((active_nodes / total_nodes) * 100) : 0;

  const statsCards = [
    {
      icon: <UsersIcon fontSize="large" />,
      value: total_users,
      label: 'Всего пользователей',
      color: theme.palette.primary.main,
    },
    {
      icon: <SpeedIcon fontSize="large" />,
      value: `${active_users} (${activeUsersPercentage}%)`,
      label: 'Активные пользователи',
      color: theme.palette.success.main,
    },
    {
      icon: <StorageIcon fontSize="large" />,
      value: `${total_traffic_gb.toFixed(2)} GB`,
      label: 'Общий трафик',
      color: theme.palette.info.main,
    },
    {
      icon: <NodesIcon fontSize="large" />,
      value: `${active_nodes} / ${total_nodes}`,
      label: 'Активные ноды',
      color: activeNodesPercentage < 50 ? theme.palette.error.main : theme.palette.success.main,
    },
  ];

  // Get recent activities from API data
  const recentActivities = stats?.recent_activities || [];

  return (
    <Layout>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1">
          Dashboard
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => refetch()}
        >
          Обновить
        </Button>
      </Box>

      {/* Stats Cards */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, mb: 4 }}>
        {statsCards.map((stat, index) => (
          <Box key={index} sx={{ flex: '1 1 250px', minWidth: '250px' }}>
            <StatCard elevation={2}>
              <StatIcon color={stat.color}>
                {stat.icon}
              </StatIcon>
              <StatValue variant="h4">
                {stat.value}
              </StatValue>
              <StatLabel variant="subtitle1">
                {stat.label}
              </StatLabel>
            </StatCard>
          </Box>
        ))}
      </Box>

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
        {/* System Status */}
        <Box sx={{ flex: '1 1 400px', minWidth: '400px' }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <CheckCircleIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="h6">
                  Статус системы
                </Typography>
              </Box>

              <Typography variant="body1" sx={{ mb: 2 }}>
                Система работает нормально
              </Typography>

              <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                Время работы: {uptime_days} дней
              </Typography>

              <Box display="flex" alignItems="center" gap={2} mt={2}>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  size="small"
                  onClick={() => navigate('/users')}
                >
                  Добавить пользователя
                </Button>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => navigate('/settings')}
                >
                  Настройки
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Box>

        {/* Recent Activities */}
        <Box sx={{ flex: '1 1 400px', minWidth: '400px' }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Последние действия
              </Typography>

              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Пользователь</TableCell>
                      <TableCell>Действие</TableCell>
                      <TableCell>Время</TableCell>
                      <TableCell>Статус</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {recentActivities.map((activity: Activity) => (
                      <TableRow key={activity.id}>
                        <TableCell>{activity.user}</TableCell>
                        <TableCell>{activity.action}</TableCell>
                        <TableCell>{activity.time}</TableCell>
                        <TableCell>
                          <Chip
                            label={activity.status}
                            color={
                              activity.status === 'success' ? 'success' :
                              activity.status === 'error' ? 'error' : 'info'
                            }
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Box>
      </Box>
    </Layout>
  );
};

export default DashboardPage;
