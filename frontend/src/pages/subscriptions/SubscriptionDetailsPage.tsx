import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  Breadcrumbs, 
  Link, 
  Tabs, 
  Tab, 
  Paper, 
  IconButton, 
  CircularProgress,
  Snackbar,
  Alert,
  useMediaQuery,
  useTheme,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from '@mui/material';
import { 
  ArrowBack as ArrowBackIcon, 
  Edit as EditIcon, 
  Delete as DeleteIcon, 
  Refresh as RefreshIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

// Components
import { PageContainer } from '../../components/PageContainer';
import { ErrorAlert } from '../../components/ErrorAlert';
import { SubscriptionOverviewTab } from '../../components/subscriptions/SubscriptionOverviewTab';
import { SubscriptionUsageTab } from '../../components/subscriptions/SubscriptionUsageTab';
import { SubscriptionLogsTab } from '../../components/subscriptions/SubscriptionLogsTab';
import { SubscriptionSecurityTab } from '../../components/subscriptions/SubscriptionSecurityTab';

// Services
import { subscriptionService } from '../../services/api/subscriptionService';
import { userService } from '../../services/api/userService';
import { nodeService } from '../../services/api/nodeService';

// Types
import { Subscription, SubscriptionStatus } from '../../types/subscription';
import { User } from '../../types/user';
import { Node } from '../../types/node';

// Utils
import { formatDate, formatDateTime } from '../../utils/formatters';

// Mock data for development
const MOCK_SUBSCRIPTION: Subscription = {
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
    { id: 'ip3', ip: '185.143.223.10', created_at: '2023-05-17T09:15:00Z', created_by: 'admin', notes: 'Подозрительная активность' },
  ],
  created_at: '2023-05-01T00:00:00Z',
  updated_at: '2023-05-20T15:30:00Z',
  expires_at: '2023-06-01T00:00:00Z',
  last_connected_at: '2023-05-20T14:30:00Z',
  last_ip: '192.168.1.1',
  is_active: true,
  notes: 'VIP клиент',
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

// Mock usage data
const MOCK_USAGE_DATA = {
  daily: Array.from({ length: 30 }, (_, i) => ({
    date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString(),
    upload: Math.floor(Math.random() * 1000000000) + 500000000, // 0.5-1.5 GB
    download: Math.floor(Math.random() * 3000000000) + 1000000000, // 1-4 GB
  })),
  hourly: Array.from({ length: 24 }, (_, i) => ({
    hour: i,
    upload: Math.floor(Math.random() * 50000000) + 10000000, // 10-60 MB
    download: Math.floor(Math.random() * 200000000) + 50000000, // 50-250 MB
  })),
};

// Mock logs data
const MOCK_LOGS = Array.from({ length: 100 }, (_, i) => ({
  id: `log_${i + 1}`,
  timestamp: new Date(Date.now() - Math.floor(Math.random() * 7 * 24 * 60 * 60 * 1000)).toISOString(),
  action: ['connect', 'disconnect', 'auth_success', 'auth_failed', 'limit_reached'][Math.floor(Math.random() * 5)],
  ip_address: `192.168.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`,
  user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
  location: {
    country: ['Россия', 'США', 'Германия', 'Китай', 'Япония'][Math.floor(Math.random() * 5)],
    city: ['Москва', 'Санкт-Петербург', 'Новосибирск', 'Екатеринбург', 'Казань'][Math.floor(Math.random() * 5)],
    isp: ['Ростелеком', 'МТС', 'Билайн', 'МегаФон', 'Yota'][Math.floor(Math.random() * 5)],
  },
  bytes_sent: Math.floor(Math.random() * 100000000) + 1000000, // 1-101 MB
  bytes_received: Math.floor(Math.random() * 500000000) + 100000000, // 100-600 MB
  duration: Math.floor(Math.random() * 3600) + 60, // 1 min - 1 hour
  status: ['success', 'warning', 'error', 'info'][Math.floor(Math.random() * 4)] as 'success' | 'warning' | 'error' | 'info',
  details: Math.random() > 0.7 ? 'Дополнительная информация об ошибке или предупреждении' : undefined,
}));

// Tab panel component
interface TabPanelProps {
  children?: React.ReactNode;
  dir?: string;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`subscription-tabpanel-${index}`}
      aria-labelledby={`subscription-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `subscription-tab-${index}`,
    'aria-controls': `subscription-tabpanel-${index}`,
  };
}

const SubscriptionDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  // State
  const [tabValue, setTabValue] = useState(0);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'info' | 'warning' }>({ 
    open: false, 
    message: '', 
    severity: 'info' 
  });
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [filters, setFilters] = useState({
    search: '',
    status: '',
    action: '',
  });
  const [pagination, setPagination] = useState({
    page: 0,
    rowsPerPage: 10,
  });

  // Fetch subscription data
  const { 
    data: subscription, 
    isLoading: isLoadingSubscription, 
    isError: isErrorSubscription, 
    error: subscriptionError,
    refetch: refetchSubscription 
  } = useQuery<Subscription, Error>(
    ['subscription', id],
    () => subscriptionService.getSubscription(id!), 
    {
      enabled: !!id,
      // For demo purposes, we'll use mock data
      // In a real app, remove this and use the actual API call
      select: (data) => ({
        ...data,
        ...MOCK_SUBSCRIPTION,
        id: id!,
      }),
    }
  );

  // Fetch user data
  const { 
    data: user, 
    isLoading: isLoadingUser, 
    isError: isErrorUser, 
    error: userError 
  } = useQuery<User | null, Error>(
    ['user', subscription?.user_id],
    () => subscription?.user_id ? userService.getUser(subscription.user_id) : Promise.resolve(null),
    {
      enabled: !!subscription?.user_id,
      // For demo purposes, we'll use mock data
      // In a real app, remove this and use the actual API call
      select: (data) => (data ? { ...data, ...MOCK_USER } : null),
    }
  );

  // Fetch node data
  const { 
    data: node, 
    isLoading: isLoadingNode, 
    isError: isErrorNode, 
    error: nodeError 
  } = useQuery<Node | null, Error>(
    ['node', subscription?.node_id],
    () => subscription?.node_id ? nodeService.getNode(subscription.node_id) : Promise.resolve(null),
    {
      enabled: !!subscription?.node_id,
      // For demo purposes, we'll use mock data
      // In a real app, remove this and use the actual API call
      select: (data) => (data ? { ...data, ...MOCK_NODE } : null),
    }
  );

  // Fetch usage data
  const { 
    data: usageData = MOCK_USAGE_DATA,
    isLoading: isLoadingUsage,
    isError: isErrorUsage,
    error: usageError,
    refetch: refetchUsage
  } = useQuery(
    ['subscription-usage', id],
    () => {
      // In a real app, this would be an API call
      return new Promise(resolve => {
        setTimeout(() => resolve(MOCK_USAGE_DATA), 500);
      });
    },
    {
      enabled: !!id && tabValue === 1, // Only fetch when on the usage tab
    }
  );

  // Fetch logs
  const { 
    data: logsData = { logs: [], total: 0 },
    isLoading: isLoadingLogs,
    isError: isErrorLogs,
    error: logsError,
    refetch: refetchLogs
  } = useQuery(
    ['subscription-logs', id, filters, pagination],
    () => {
      // In a real app, this would be an API call with filters and pagination
      return new Promise<{ logs: any[]; total: number }>(resolve => {
        setTimeout(() => {
          // Apply filters
          let filteredLogs = [...MOCK_LOGS];
          
          if (filters.search) {
            const searchLower = filters.search.toLowerCase();
            filteredLogs = filteredLogs.filter(
              log => 
                log.ip_address.includes(filters.search) ||
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
          const start = pagination.page * pagination.rowsPerPage;
          const end = start + pagination.rowsPerPage;
          const paginatedLogs = filteredLogs.slice(start, end);
          
          resolve({
            logs: paginatedLogs,
            total: filteredLogs.length,
          });
        }, 500);
      });
    },
    {
      enabled: !!id && tabValue === 2, // Only fetch when on the logs tab
      keepPreviousData: true,
    }
  );

  // Mutations
  const deleteSubscriptionMutation = useMutation(
    () => subscriptionService.deleteSubscription(id!),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['subscriptions']);
        setSnackbar({ open: true, message: 'Подписка успешно удалена', severity: 'success' });
        setTimeout(() => navigate('/subscriptions'), 1500);
      },
      onError: (error: Error) => {
        setSnackbar({ open: true, message: `Ошибка при удалении подписки: ${error.message}`, severity: 'error' });
      },
    }
  );

  const toggleSubscriptionStatusMutation = useMutation(
    (status: SubscriptionStatus) => subscriptionService.updateSubscription(id!, { status }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['subscription', id]);
        queryClient.invalidateQueries(['subscriptions']);
        setSnackbar({ 
          open: true, 
          message: `Статус подписки успешно обновлен`, 
          severity: 'success' 
        });
      },
      onError: (error: Error) => {
        setSnackbar({ 
          open: true, 
          message: `Ошибка при обновлении статуса: ${error.message}`, 
          severity: 'error' 
        });
      },
    }
  );

  const updateIpWhitelistMutation = useMutation(
    (ips: string[]) => subscriptionService.updateSubscriptionIpWhitelist(id!, ips),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['subscription', id]);
        setSnackbar({ 
          open: true, 
          message: 'Белый список IP-адресов обновлен', 
          severity: 'success' 
        });
      },
      onError: (error: Error) => {
        setSnackbar({ 
          open: true, 
          message: `Ошибка при обновлении белого списка: ${error.message}`, 
          severity: 'error' 
        });
      },
    }
  );

  const updateIpBlacklistMutation = useMutation(
    (ips: string[]) => subscriptionService.updateSubscriptionIpBlacklist(id!, ips),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['subscription', id]);
        setSnackbar({ 
          open: true, 
          message: 'Черный список IP-адресов обновлен', 
          severity: 'success' 
        });
      },
      onError: (error: Error) => {
        setSnackbar({ 
          open: true, 
          message: `Ошибка при обновлении черного списка: ${error.message}`, 
          severity: 'error' 
        });
      },
    }
  );

  const toggleIpRestrictionsMutation = useMutation(
    (enabled: boolean) => 
      subscriptionService.updateSubscription(id!, { 
        ip_restriction: enabled ? 'enabled' : 'disabled' 
      }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['subscription', id]);
        setSnackbar({ 
          open: true, 
          message: 'Настройки ограничений по IP обновлены', 
          severity: 'success' 
        });
      },
      onError: (error: Error) => {
        setSnackbar({ 
          open: true, 
          message: `Ошибка при обновлении ограничений: ${error.message}`, 
          severity: 'error' 
        });
      },
    }
  );

  // Handlers
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleDeleteClick = () => {
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = () => {
    deleteSubscriptionMutation.mutate();
    setDeleteDialogOpen(false);
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
  };

  const handleSnackbarClose = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  const handleToggleStatus = () => {
    if (!subscription) return;
    
    const newStatus = subscription.status === 'active' ? 'suspended' : 'active';
    toggleSubscriptionStatusMutation.mutate(newStatus);
  };

  const handleUpdateIpWhitelist = async (ips: string[]) => {
    await updateIpWhitelistMutation.mutateAsync(ips);
  };

  const handleUpdateIpBlacklist = async (ips: string[]) => {
    await updateIpBlacklistMutation.mutateAsync(ips);
  };

  const handleToggleIpRestrictions = async (enabled: boolean) => {
    await toggleIpRestrictionsMutation.mutateAsync(enabled);
  };

  const handlePageChange = (newPage: number) => {
    setPagination(prev => ({ ...prev, page: newPage }));
  };

  const handleRowsPerPageChange = (newRowsPerPage: number) => {
    setPagination(prev => ({
      page: 0, // Reset to first page
      rowsPerPage: newRowsPerPage,
    }));
  };

  const handleFilterChange = (newFilters: { search: string; status: string; action: string }) => {
    setFilters(newFilters);
    setPagination(prev => ({ ...prev, page: 0 })); // Reset to first page when filters change
  };

  const handleRefresh = () => {
    if (tabValue === 0) {
      refetchSubscription();
    } else if (tabValue === 1) {
      refetchUsage();
    } else if (tabValue === 2) {
      refetchLogs();
    }
  };

  // Loading and error states
  const isLoading = isLoadingSubscription || isLoadingUser || isLoadingNode;
  const isError = isErrorSubscription || isErrorUser || isErrorNode;
  const error = subscriptionError || userError || nodeError;

  if (isLoading) {
    return (
      <PageContainer>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
          <CircularProgress />
        </Box>
      </PageContainer>
    );
  }

  if (isError || !subscription) {
    return (
      <PageContainer>
        <ErrorAlert 
          message={error?.message || 'Не удалось загрузить данные о подписке'}
          onRetry={() => {
            refetchSubscription();
            if (subscription?.user_id) {
              queryClient.invalidateQueries(['user', subscription.user_id]);
            }
            if (subscription?.node_id) {
              queryClient.invalidateQueries(['node', subscription.node_id]);
            }
          }}
        />
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      {/* Breadcrumbs */}
      <Box mb={3}>
        <Breadcrumbs aria-label="breadcrumb">
          <Link component={RouterLink} to="/" color="inherit">
            Главная
          </Link>
          <Link component={RouterLink} to="/subscriptions" color="inherit">
            Подписки
          </Link>
          <Typography color="text.primary">
            {subscription.id}
          </Typography>
        </Breadcrumbs>
      </Box>

      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center">
          <IconButton 
            component={RouterLink} 
            to="/subscriptions" 
            sx={{ mr: 1 }}
            aria-label="назад к списку подписок"
          >
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h4" component="h1">
            Подписка #{subscription.id.split('_').pop()?.toUpperCase()}
          </Typography>
          
          <Box ml={2} display="flex" alignItems="center">
            <Box
              sx={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                backgroundColor: subscription.status === 'active' ? 'success.main' : 'error.main',
                mr: 1,
              }}
            />
            <Typography variant="body1" color="textSecondary">
              {subscription.status === 'active' ? 'Активна' : 'Приостановлена'}
            </Typography>
          </Box>
        </Box>
        
        <Box>
          <Button
            variant="outlined"
            color="primary"
            startIcon={<EditIcon />}
            component={RouterLink}
            to={`/subscriptions/${id}/edit`}
            sx={{ mr: 1 }}
          >
            Редактировать
          </Button>
          <Button
            variant="outlined"
            color={subscription.status === 'active' ? 'warning' : 'success'}
            startIcon={<RefreshIcon />}
            onClick={handleToggleStatus}
            disabled={toggleSubscriptionStatusMutation.isLoading}
            sx={{ mr: 1 }}
          >
            {subscription.status === 'active' ? 'Приостановить' : 'Активировать'}
          </Button>
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={handleDeleteClick}
            disabled={deleteSubscriptionMutation.isLoading}
          >
            Удалить
          </Button>
        </Box>
      </Box>

      {/* Tabs */}
      <Box sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs 
            value={tabValue} 
            onChange={handleTabChange} 
            aria-label="subscription details tabs"
            variant={isMobile ? 'scrollable' : 'standard'}
            scrollButtons={isMobile ? 'auto' : false}
            allowScrollButtonsMobile
          >
            <Tab label="Обзор" {...a11yProps(0)} />
            <Tab label="Использование" {...a11yProps(1)} />
            <Tab label="История подключений" {...a11yProps(2)} />
            <Tab label="Безопасность" {...a11yProps(3)} />
          </Tabs>
        </Box>

        {/* Tab Panels */}
        <Paper sx={{ mt: 2, mb: 4 }}>
          <TabPanel value={tabValue} index={0}>
            <SubscriptionOverviewTab 
              subscription={subscription}
              user={user || undefined}
              node={node || undefined}
              onToggleStatus={handleToggleStatus}
              isUpdating={toggleSubscriptionStatusMutation.isLoading}
            />
          </TabPanel>
          
          <TabPanel value={tabValue} index={1}>
            <SubscriptionUsageTab 
              usageData={usageData}
              isLoading={isLoadingUsage}
              isError={isErrorUsage}
              error={usageError}
              onRefresh={refetchUsage}
            />
          </TabPanel>
          
          <TabPanel value={tabValue} index={2}>
            <SubscriptionLogsTab 
              logs={logsData.logs}
              totalLogs={logsData.total}
              page={pagination.page}
              rowsPerPage={pagination.rowsPerPage}
              onPageChange={handlePageChange}
              onRowsPerPageChange={handleRowsPerPageChange}
              onRefresh={handleRefresh}
              isLoading={isLoadingLogs}
              filters={filters}
              onFilterChange={handleFilterChange}
            />
          </TabPanel>
          
          <TabPanel value={tabValue} index={3}>
            <SubscriptionSecurityTab 
              subscription={{
                ...subscription,
                enforce_ip_restrictions: subscription.ip_restriction === 'enabled',
              }}
              onUpdateIpWhitelist={handleUpdateIpWhitelist}
              onUpdateIpBlacklist={handleUpdateIpBlacklist}
              onToggleIpRestrictions={handleToggleIpRestrictions}
              isLoading={isLoading}
              isUpdating={
                updateIpWhitelistMutation.isLoading || 
                updateIpBlacklistMutation.isLoading ||
                toggleIpRestrictionsMutation.isLoading
              }
            />
          </TabPanel>
        </Paper>
      </Box>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
        aria-labelledby="delete-dialog-title"
        aria-describedby="delete-dialog-description"
      >
        <DialogTitle id="delete-dialog-title">
          Подтверждение удаления
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="delete-dialog-description">
            Вы уверены, что хотите удалить подписку? Это действие нельзя отменить. 
            Пользователь больше не сможет подключаться к VPN с этой подпиской.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel} color="primary">
            Отмена
          </Button>
          <Button 
            onClick={handleDeleteConfirm} 
            color="error" 
            variant="contained"
            disabled={deleteSubscriptionMutation.isLoading}
            startIcon={
              deleteSubscriptionMutation.isLoading ? (
                <CircularProgress size={20} color="inherit" />
              ) : (
                <DeleteIcon />
              )
            }
          >
            {deleteSubscriptionMutation.isLoading ? 'Удаление...' : 'Удалить'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={handleSnackbarClose} 
          severity={snackbar.severity} 
          variant="filled"
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </PageContainer>
  );
};

export default SubscriptionDetailsPage;
