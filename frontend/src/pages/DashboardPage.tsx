import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Grid,
  Paper,
  Typography,
  CircularProgress,
  Container,
  useTheme,
} from '@mui/material';
import {
  People as UsersIcon,
  Dns as NodesIcon,
  Speed as SpeedIcon,
  Storage as StorageIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { getDashboardStats } from '../services/dashboardService';

// Styled components
const StatCard = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  height: '100%',
  borderRadius: theme.shape.borderRadius * 2,
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
  
  // Fetch dashboard data
  const { data: stats, isLoading, error } = useQuery(['dashboard', 'stats'], getDashboardStats, {
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

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Панель управления
      </Typography>
      
      <Typography variant="subtitle1" color="textSecondary" paragraph>
        Обзор системы и статистика
      </Typography>

      {/* Stats Grid */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {statsCards.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <StatCard elevation={3}>
              <StatIcon color={stat.color}>
                {stat.icon}
              </StatIcon>
              <StatValue variant="h3">{stat.value}</StatValue>
              <StatLabel variant="subtitle1">{stat.label}</StatLabel>
            </StatCard>
          </Grid>
        ))}
      </Grid>

      {/* System Status */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, borderRadius: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Статус системы
            </Typography>
            
            <Box display="flex" alignItems="center" mb={2}>
              <CheckCircleIcon color="success" sx={{ mr: 1 }} />
              <Typography>Сервер работает стабильно</Typography>
            </Box>
            
            <Box display="flex" alignItems="center" mb={2}>
              <Typography variant="body2" color="textSecondary">
                Время работы: {uptime_days} дней
              </Typography>
            </Box>
            
            <Box display="flex" alignItems="center" mb={2}>
              <WarningIcon color="warning" sx={{ mr: 1 }} />
              <Typography>Новые обновления доступны</Typography>
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, borderRadius: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Быстрые действия
            </Typography>
            
            <Box display="flex" flexDirection="column" gap={2}>
              <Typography variant="body2" color="textSecondary">
                • <a href="/users/new" style={{ color: theme.palette.primary.main, textDecoration: 'none' }}>Добавить пользователя</a>
              </Typography>
              <Typography variant="body2" color="textSecondary">
                • <a href="/nodes" style={{ color: theme.palette.primary.main, textDecoration: 'none' }}>Управление нодами</a>
              </Typography>
              <Typography variant="body2" color="textSecondary">
                • <a href="/settings" style={{ color: theme.palette.primary.main, textDecoration: 'none' }}>Настройки системы</a>
              </Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default DashboardPage;
