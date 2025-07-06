import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { format, subDays, formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Divider,
  Button,
  IconButton,
  Tabs,
  Tab,
  Chip,
  LinearProgress,
  Tooltip,
  useTheme,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  FormControlLabel,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Snackbar,
  SelectChangeEvent,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  FileDownload as FileDownloadIcon,
  Speed as SpeedIcon,
  CalendarToday as CalendarIcon,
  DataUsage as DataUsageIcon,
  Person as PersonIcon,
  Dns as NodeIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  CloudQueue as CloudQueueIcon,
  CloudOff as CloudOffIcon,
  ContentCopy as ContentCopyIcon,
  History as HistoryIcon,
  BarChart as BarChartIcon,
  Timeline as TimelineIcon,
  Receipt as ReceiptIcon,
  Security as SecurityIcon,
  SettingsEthernet as SettingsEthernetIcon,
  EventNote as EventNoteIcon,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { styled } from '@mui/material/styles';
import { 
  getSubscription, 
  updateSubscription, 
  deleteSubscription,
  renewSubscription,
  toggleSubscriptionStatus,
  getSubscriptionUsage,
  getSubscriptionLogs,
  updateIpWhitelist,
  updateIpBlacklist,
  Subscription,
  SubscriptionStatus,
  SubscriptionPlan,
} from '../services/subscriptionService';
import { getUsers } from '../services/userService';
import { getNodes } from '../services/nodeService';
import { formatBytes, formatDate, formatDateTime } from '../utils/formatters';

// Styled components
const StatCard = styled(Card)(({ theme }) => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  transition: 'transform 0.2s, box-shadow 0.2s',
  '&:hover': {
    transform: 'translateY(-4px)',
    boxShadow: theme.shadows[8],
  },
}));

const StatusChip = styled(Chip)(({ theme, status }) => ({
  fontWeight: 'bold',
  backgroundColor: status === 'active' 
    ? theme.palette.success.light 
    : status === 'expired'
    ? theme.palette.error.light
    : theme.palette.warning.light,
  color: status === 'active' 
    ? theme.palette.success.contrastText 
    : status === 'expired'
    ? theme.palette.error.contrastText
    : theme.palette.warning.contrastText,
}));

const SubscriptionDetailsPage: React.FC = () => {
  const { subscriptionId } = useParams<{ subscriptionId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const theme = useTheme();
  
  // State
  const [activeTab, setActiveTab] = useState('overview');
  const [timeRange, setTimeRange] = useState('7days');
  const [openEditDialog, setOpenEditDialog] = useState(false);
  const [openDeleteDialog, setOpenDeleteDialog] = useState(false);
  const [openRenewDialog, setOpenRenewDialog] = useState(false);
  const [openIpWhitelistDialog, setOpenIpWhitelistDialog] = useState(false);
  const [openIpBlacklistDialog, setOpenIpBlacklistDialog] = useState(false);
  const [openSnackbar, setOpenSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [formData, setFormData] = useState<Partial<Subscription>>({});
  const [ipWhitelist, setIpWhitelist] = useState<string[]>([]);
  const [ipBlacklist, setIpBlacklist] = useState<string[]>([]);
  const [newIp, setNewIp] = useState('');
  
  // Fetch subscription data
  const { 
    data: subscriptionData, 
    isLoading, 
    isError,
    refetch: refetchSubscription,
  } = useQuery(
    ['subscription', subscriptionId], 
    () => getSubscription(subscriptionId!)
  );
  
  const { data: usersData } = useQuery(
    ['users'], 
    getUsers,
    { enabled: !!subscriptionId }
  );
  
  const { data: nodesData } = useQuery(
    ['nodes'], 
    getNodes,
    { enabled: !!subscriptionId }
  );
  
  // Calculate date range for usage data
  const getDateRange = () => {
    const now = new Date();
    switch (timeRange) {
      case '24h':
        return {
          startDate: format(subDays(now, 1), 'yyyy-MM-dd'),
          endDate: format(now, 'yyyy-MM-dd'),
          granularity: 'hour' as const,
        };
      case '7days':
        return {
          startDate: format(subDays(now, 7), 'yyyy-MM-dd'),
          endDate: format(now, 'yyyy-MM-dd'),
          granularity: 'day' as const,
        };
      case '30days':
        return {
          startDate: format(subDays(now, 30), 'yyyy-MM-dd'),
          endDate: format(now, 'yyyy-MM-dd'),
          granularity: 'day' as const,
        };
      case '90days':
        return {
          startDate: format(subDays(now, 90), 'yyyy-MM-dd'),
          endDate: format(now, 'yyyy-MM-dd'),
          granularity: 'week' as const,
        };
      default:
        return {
          startDate: format(subDays(now, 7), 'yyyy-MM-dd'),
          endDate: format(now, 'yyyy-MM-dd'),
          granularity: 'day' as const,
        };
    }
  };
  
  const { startDate, endDate, granularity } = getDateRange();
  
  // Fetch usage data
  const { data: usageData, isLoading: isLoadingUsage } = useQuery(
    ['subscription-usage', subscriptionId, startDate, endDate, granularity],
    () => getSubscriptionUsage(subscriptionId!, { startDate, endDate, granularity }),
    { enabled: !!subscriptionId && activeTab === 'usage' }
  );
  
  // Fetch connection logs
  const [logsPage, setLogsPage] = useState(0);
  const [logsPerPage, setLogsPerPage] = useState(10);
  
  const { data: logsData, isLoading: isLoadingLogs } = useQuery(
    ['subscription-logs', subscriptionId, logsPage, logsPerPage],
    () => getSubscriptionLogs(subscriptionId!, { 
      offset: logsPage * logsPerPage, 
      limit: logsPerPage 
    }),
    { 
      enabled: !!subscriptionId && activeTab === 'logs',
      keepPreviousData: true,
    }
  );
  
  // ... rest of the component code will be added in the next part ...
  
  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }
  
  if (isError || !subscriptionData?.data) {
    return (
      <Box textAlign="center" p={3}>
        <Alert severity="error">
          Ошибка при загрузке данных подписки. Пожалуйста, попробуйте снова.
        </Alert>
        <Button 
          variant="outlined" 
          color="primary" 
          onClick={() => refetchSubscription()}
          sx={{ mt: 2 }}
        >
          Повторить попытку
        </Button>
      </Box>
    );
  }
  
  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center">
          <IconButton onClick={() => navigate(-1)} sx={{ mr: 1 }}>
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h4" component="h1">
            Подписка #{subscriptionData.data.id.substring(0, 8)}...
          </Typography>
        </Box>
        
        <Box>
          <Button
            variant="outlined"
            color="primary"
            startIcon={<RefreshIcon />}
            onClick={() => refetchSubscription()}
            sx={{ mr: 1 }}
          >
            Обновить
          </Button>
          <Button
            variant="contained"
            color="primary"
            startIcon={<EditIcon />}
            onClick={() => setOpenEditDialog(true)}
          >
            Редактировать
          </Button>
        </Box>
      </Box>
      
      {/* Tabs */}
      <Paper sx={{ mb: 2 }}>
        <Tabs
          value={activeTab}
          onChange={(e, newValue) => setActiveTab(newValue)}
          indicatorColor="primary"
          textColor="primary"
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab label="Обзор" value="overview" icon={<SpeedIcon />} iconPosition="start" />
          <Tab label="Использование" value="usage" icon={<BarChartIcon />} iconPosition="start" />
          <Tab label="История подключений" value="logs" icon={<HistoryIcon />} iconPosition="start" />
          <Tab label="Настройки безопасности" value="security" icon={<SecurityIcon />} iconPosition="start" />
        </Tabs>
      </Paper>
      
      {/* Tab Content */}
      <Box>
        {activeTab === 'overview' && (
          <Typography>Overview content will be here</Typography>
        )}
        
        {activeTab === 'usage' && (
          <Typography>Usage statistics will be here</Typography>
        )}
        
        {activeTab === 'logs' && (
          <Typography>Connection logs will be here</Typography>
        )}
        
        {activeTab === 'security' && (
          <Typography>Security settings will be here</Typography>
        )}
      </Box>
      
      {/* Snackbar for notifications */}
      <Snackbar
        open={openSnackbar}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity="success" sx={{ width: '100%' }}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default SubscriptionDetailsPage;
