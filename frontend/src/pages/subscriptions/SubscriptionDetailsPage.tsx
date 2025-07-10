import React, { useState } from 'react';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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
  Tooltip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Alert,
  Snackbar,
} from '@mui/material';
import { 
  ArrowBack as ArrowBackIcon, 
  Edit as EditIcon, 
  Delete as DeleteIcon, 
  Refresh as RefreshIcon,
} from '@mui/icons-material';

// --- Service Imports ---
import { 
  getSubscription, 
  updateSubscription, 
  deleteSubscription, 
  getSubscriptionUsage, 
  getSubscriptionLogs,
  updateIpWhitelist,
  updateIpBlacklist,
  toggleSubscriptionStatus,
  Subscription as SubscriptionType,
  Subscription as SubscriptionInterface
} from '../../services/subscriptionService';
import { getUser, User as UserType } from '../../services/userService';
import { getNode, Node as NodeType } from '../../services/nodeService';

// --- Type Definitions ---
type TimeRange = '24h' | '7d' | '30d';

interface IpAddress {
  id: string;
  address: string;
  created_at: string;
  updated_at: string;
}

interface ExtendedSubscription extends Omit<SubscriptionInterface, 'status' | 'ip_whitelist' | 'ip_blacklist' | 'ip_restriction'> {
  ip_whitelist: (string | IpAddress)[];
  ip_blacklist: (string | IpAddress)[];
  status: 'active' | 'suspended' | 'expired';
  enforce_ip_restrictions: boolean;
  traffic_used: number;
  traffic_limit: number;
  ip_restriction: 'enabled' | 'disabled';
  expires_at: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  user_id: string;
  node_id: string;
  plan_id: string;
  last_connected?: string;
}

interface LogEntry {
  id: string;
  timestamp: string;
  action: string;
  ip_address: string;
  status: 'error' | 'success' | 'info' | 'warning';
  details: any;
}

interface LogFilters {
  level: string;
  search: string;
  status: string;
  action: string;
  dateRange: { start: Date | null; end: Date | null };
  page: number;
  limit: number;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

interface ExtendedUserType extends UserType {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: string;
  status: 'active' | 'suspended';
  created_at: string;
  updated_at: string;
}

interface ExtendedNodeType extends NodeType {
  id: string;
  name: string;
  hostname: string;
  ip_address: string;
  city: string;
  country: string;
  current_users: number;
  status: 'online' | 'offline' | 'maintenance';
  load_average: number;
  created_at: string;
  updated_at: string;
}

interface SubscriptionOverviewTabProps {
  subscription: ExtendedSubscription;
  user?: ExtendedUserType;
  node?: ExtendedNodeType;
  onToggleStatus: () => void;
  isUpdating?: boolean;
  isLoading?: boolean;
  onRefresh: () => void;
}

interface SubscriptionUsageTabProps {
  subscription: ExtendedSubscription;
  usageData: Array<{ date: string; bytes_used: number }>;
  timeRange: TimeRange;
  onTimeRangeChange: (range: string) => void;
  onRefresh: () => void;
  isLoading?: boolean;
  error?: any;
}

interface SubscriptionSecurityTabProps {
  subscription: {
    id: string;
    ip_whitelist: string[];
    ip_blacklist: string[];
    enforce_ip_restrictions: boolean;
  };
  onUpdateIpWhitelist: (ips: string[]) => Promise<void>;
  onUpdateIpBlacklist: (ips: string[]) => Promise<void>;
  onToggleIpRestrictions: (enabled: boolean) => Promise<void>;
  isLoading?: boolean;
  isUpdating?: boolean;
}

interface SubscriptionLogsTabProps {
  logs: LogEntry[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
  filters: {
    search: string;
    status: string;
    action: string;
  };
  onPageChange: (page: number) => void;
  onRowsPerPageChange: (rowsPerPage: number) => void;
  onFilterChange: (filters: { search?: string; status?: string; action?: string }) => void;
  onRefresh: () => void;
  isLoading?: boolean;
  error?: any;
}

// --- Child Component Imports ---
import SubscriptionOverviewTab from '../../components/subscriptions/SubscriptionOverviewTab';
import SubscriptionUsageTab from '../../components/subscriptions/SubscriptionUsageTab';
import SubscriptionLogsTab from '../../components/subscriptions/SubscriptionLogsTab';
import SubscriptionSecurityTab from '../../components/subscriptions/SubscriptionSecurityTab';

// --- Helper Components ---
const PageContainer = ({ children }: { children: React.ReactNode }) => (
  <Box sx={{ p: 3 }}>{children}</Box>
);

const ErrorAlert = ({ error }: { error: Error | null }) => {
  if (!error) return null;
  return <Alert severity="error">{error.message}</Alert>;
};

// --- TabPanel Component ---
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
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `subscription-tab-${index}`,
    'aria-controls': `subscription-tabpanel-${index}`,
  };
}

// --- Main Component ---
const SubscriptionDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>(); // Get subscription ID from URL
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  const [tab, setTab] = useState(0);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'info' as 'info' | 'success' | 'warning' | 'error'
  });
  
  const [timeRange, setTimeRange] = useState<TimeRange>('7d');
  
  const [logFilters, setLogFilters] = useState({
    level: 'all',
    search: '',
    status: '',
    action: '',
    dateRange: { start: null as Date | null, end: null as Date | null },
    page: 1,
    limit: 10
  });
  
  const [logPagination, setLogPagination] = useState({
    page: 1,
    limit: 10
  });
  
  // --- Query for Subscription Data ---
  const { 
    data: subscriptionData, 
    isLoading: isLoadingSubscription, 
    error: subscriptionError, 
    refetch: refetchSubscription 
  } = useQuery({
    queryKey: ['subscription', id],
    queryFn: async () => {
      if (!id) throw new Error('Subscription ID is required');
      const subscription = await getSubscription(id);
      
      // Get user data if subscription has user_id
      let user: ExtendedUserType | null = null;
      if ((subscription as any).data.user_id) {
        try {
          user = await getUser((subscription as any).data.user_id) as unknown as ExtendedUserType;
        } catch (err) {
          console.error('Failed to fetch user:', err);
        }
      }
      
      // Get node data if subscription has node_id
      let node: ExtendedNodeType | null = null;
      if ((subscription as any).data.node_id) {
        try {
          node = await getNode((subscription as any).data.node_id) as unknown as ExtendedNodeType;
        } catch (err) {
          console.error('Failed to fetch node:', err);
        }
      }
      
      return { 
        subscription: (subscription as any).data as unknown as ExtendedSubscription, 
        user: user as ExtendedUserType, 
        node: node as ExtendedNodeType
      };
    },
    staleTime: 60 * 1000, // 1 minute
    enabled: !!id
  });
  
  // Helper function to get date range
  const getDateRange = (range: string) => {
    const end = new Date();
    const start = new Date();
    
    switch (range) {
      case '24h':
        start.setDate(start.getDate() - 1);
        break;
      case '7d':
        start.setDate(start.getDate() - 7);
        break;
      case '30d':
        start.setDate(start.getDate() - 30);
        break;
      default:
        start.setDate(start.getDate() - 7);
    }
    
    return { start, end };
  };
  
  // --- Query for Usage Data ---
  const { 
    data: usageData, 
    isLoading: isLoadingUsage, 
    error: usageError, 
    refetch: refetchUsage 
  } = useQuery({
    queryKey: ['subscriptionUsage', id, timeRange],
    queryFn: async () => {
      if (!id) throw new Error('Subscription ID is required');
      const dateRange = getDateRange(timeRange);
      return await getSubscriptionUsage(id, {
        startDate: dateRange.start.toISOString(),
        endDate: dateRange.end.toISOString(),
        granularity: 'day'
      });
    },
    staleTime: 60 * 1000, // 1 minute
    enabled: !!id
  });
  
  // --- Query for Logs ---
  const { 
    data: logsData, 
    isLoading: isLoadingLogs,
    error: logsError,
    refetch: refetchLogs 
  } = useQuery({
    queryKey: ['subscriptionLogs', id, logPagination, logFilters],
    queryFn: async () => {
      if (!id) throw new Error('Subscription ID is required');
      return await getSubscriptionLogs(id, {
        limit: logPagination.limit,
        offset: (logPagination.page - 1) * logPagination.limit,
        sort: 'desc'
      });
    },
    enabled: !!id && tab === 2
  });
  
  // Update IP whitelist mutation
  const updateWhitelistMutation = useMutation({
    mutationFn: (ips: string[]) => updateIpWhitelist(id!, ips),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscription', id] });
    }
  });
  
  // Toggle IP restrictions mutation
  const toggleIpRestrictionsMutation = useMutation({
    mutationFn: (enabled: boolean) => updateSubscription(id!, { notes: enabled ? 'IP restrictions enabled' : 'IP restrictions disabled' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscription', id] });
    }
  });
  
  // --- Mutations ---
  const updateStatusMutation = useMutation({
    mutationFn: async (newStatus: 'active' | 'suspended') => {
      if (!id) throw new Error('Subscription ID is required');
      await updateSubscription(id, { status: newStatus });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscription', id] });
      setSnackbar({
        open: true,
        message: 'Subscription status updated',
        severity: 'success'
      });
    },
    onError: (error) => {
      console.error('Failed to update subscription status:', error);
      setSnackbar({
        open: true,
        message: 'Failed to update status',
        severity: 'error'
      });
    }
  });
  
  const deleteMutation = useMutation({
    mutationFn: async () => {
      if (!id) throw new Error('Subscription ID is required');
      await deleteSubscription(id);
    },
    onSuccess: () => {
      setSnackbar({
        open: true,
        message: 'Subscription deleted successfully',
        severity: 'success'
      });
      setTimeout(() => {
        navigate('/subscriptions');
      }, 2000);
    },
    onError: (error) => {
      console.error('Failed to delete subscription:', error);
      setSnackbar({
        open: true,
        message: 'Failed to delete subscription',
        severity: 'error'
      });
    }
  });
  
  // --- Handlers ---
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTab(newValue);
  };
  
  const handleTimeRangeChange = (range: string) => {
    setTimeRange(range as TimeRange);
  };
  
  const handleRefresh = () => {
    refetchSubscription();
    refetchUsage();
    refetchLogs();
  };
  
  const handleToggleStatus = () => {
    if (!subscriptionData) return;
    const newStatus = subscriptionData.subscription.status === 'active' ? 'suspended' : 'active';
    updateStatusMutation.mutate(newStatus);
  };
  
  const handleDeleteClick = () => {
    setDeleteDialogOpen(true);
  };
  
  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
  };
  
  const handleDeleteConfirm = () => {
    deleteMutation.mutate();
  };
  
  const handleLogsPageChange = (newPage: number) => {
    setLogPagination(prev => ({
      ...prev,
      page: newPage
    }));
  };
  
  const handleLogsRowsPerPageChange = (newRowsPerPage: number) => {
    setLogPagination({ page: 1, limit: newRowsPerPage });
  };
  
  const handleLogsFilterChange = (filters: { search?: string; status?: string; action?: string }) => {
    setLogFilters(prev => ({
      ...prev,
      ...filters
    }));
    setLogPagination(prev => ({
      ...prev,
      page: 1
    }));
  };
  
  const handleUpdateIpWhitelist = async (ips: string[]) => {
    if (!id) return;
    try {
      await updateIpWhitelist(id, ips);
      await queryClient.invalidateQueries({ queryKey: ['subscription', id] });
      setSnackbar({
        open: true,
        message: 'IP whitelist updated',
        severity: 'success'
      });
    } catch (error) {
      console.error('Failed to update IP whitelist:', error);
      setSnackbar({
        open: true,
        message: 'Failed to update IP whitelist',
        severity: 'error'
      });
    }
  };
  
  const handleUpdateIpBlacklist = async (ips: string[]) => {
    if (!id) return;
    try {
      await updateIpBlacklist(id, ips);
      await queryClient.invalidateQueries({ queryKey: ['subscription', id] });
      setSnackbar({
        open: true,
        message: 'IP blacklist updated',
        severity: 'success'
      });
    } catch (error) {
      console.error('Failed to update IP blacklist:', error);
      setSnackbar({
        open: true,
        message: 'Failed to update IP blacklist',
        severity: 'error'
      });
    }
  };
  
  const handleToggleIpRestrictions = async (enabled: boolean) => {
    if (!id) return;
    try {
      await updateSubscription(id, { notes: enabled ? 'IP restrictions enabled' : 'IP restrictions disabled' });
      await queryClient.invalidateQueries({ queryKey: ['subscription', id] });
      setSnackbar({
        open: true,
        message: `IP restrictions ${enabled ? 'enabled' : 'disabled'}`,
        severity: 'success'
      });
    } catch (error) {
      console.error('Failed to toggle IP restrictions:', error);
      setSnackbar({
        open: true,
        message: 'Failed to update IP restrictions',
        severity: 'error'
      });
    }
  };
  
  // --- Loading & Error States ---
  if (isLoadingSubscription) {
    return (
      <PageContainer>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '300px' }}>
          <CircularProgress />
        </Box>
      </PageContainer>
    );
  }
  
  if (subscriptionError) {
    return (
      <PageContainer>
        <Alert severity="error">
          Failed to load subscription data. Please try again later.
        </Alert>
      </PageContainer>
    );
  }
  
  if (!subscriptionData) {
    return (
      <PageContainer>
        <Alert severity="warning">
          Subscription not found.
        </Alert>
      </PageContainer>
    );
  }
  
  // --- Render ---
  return (
    <PageContainer>
      {/* Breadcrumbs */}
      <Breadcrumbs aria-label="breadcrumb" sx={{ mb: 2 }}>
        <Link component={RouterLink} to="/">
          Home
        </Link>
        <Link component={RouterLink} to="/subscriptions">
          Subscriptions
        </Link>
        <Typography color="text.primary">Subscription Details</Typography>
      </Breadcrumbs>
      
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <IconButton 
          onClick={() => navigate('/subscriptions')} 
          sx={{ mr: 2 }}
          aria-label="Back to subscriptions"
        >
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4" component="h1" sx={{ flexGrow: 1 }}>
          Subscription Details
        </Typography>
        <Tooltip title="Refresh data">
          <IconButton onClick={handleRefresh} sx={{ mr: 1 }}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Edit subscription">
          <IconButton 
            onClick={() => navigate(`/subscriptions/edit/${id}`)} 
            sx={{ mr: 1 }}
          >
            <EditIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Delete subscription">
          <IconButton 
            color="error" 
            onClick={handleDeleteClick}
          >
            <DeleteIcon />
          </IconButton>
        </Tooltip>
      </Box>
      
      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tab} onChange={handleTabChange} aria-label="subscription details tabs">
          <Tab label="Overview" {...a11yProps(0)} />
          <Tab label="Usage" {...a11yProps(1)} />
          <Tab label="Logs" {...a11yProps(2)} />
          <Tab label="Security" {...a11yProps(3)} />
        </Tabs>
      </Box>
      
      {/* Tab Content */}
      <TabPanel value={tab} index={0}>
        {subscriptionData && (
          <SubscriptionOverviewTab
            subscription={subscriptionData.subscription as any}
            user={subscriptionData.user}
            node={subscriptionData.node}
            onToggleStatus={handleToggleStatus}
            isUpdating={updateStatusMutation.isPending}
            isLoading={isLoadingSubscription}
            onRefresh={handleRefresh}
          />
        )}
      </TabPanel>
      
      <TabPanel value={tab} index={1}>
        {subscriptionData ? (
          <SubscriptionUsageTab
            subscription={subscriptionData.subscription as any}
            usageData={(usageData as any)?.data || []}
            timeRange={timeRange}
            onTimeRangeChange={handleTimeRangeChange}
            onRefresh={handleRefresh}
            isLoading={isLoadingUsage}

          />
        ) : isLoadingUsage ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Alert severity="error">Failed to load usage data</Alert>
        )}
      </TabPanel>
      
      <TabPanel value={tab} index={2}>
        {isLoadingLogs ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : logsError ? (
          <Alert severity="error">Failed to load logs</Alert>
        ) : (
          (() => {
            const formattedLogs = (logsData?.data || []).map(log => ({
              id: `log-${Math.random().toString(36).substr(2, 9)}`,
              timestamp: log.timestamp || new Date().toISOString(),
              action: log.action || 'unknown',
              ip_address: log.ip || '0.0.0.0',
              status: ((log as any).status as 'error' | 'success' | 'info' | 'warning') || 'info',
              details: typeof log.details === 'string' ? log.details : JSON.stringify(log.details || {})
            }));

            return (
              <SubscriptionLogsTab
                logs={formattedLogs}
                totalLogs={(logsData as any)?.total || 0}
                page={logPagination.page}
                rowsPerPage={logPagination.limit}
                filters={{
                  search: logFilters.search || '',
                  status: logFilters.status || '',
                  action: logFilters.action || ''
                }}
                isLoading={isLoadingLogs}
                onPageChange={handleLogsPageChange}
                onRowsPerPageChange={handleLogsRowsPerPageChange}
                onFilterChange={handleLogsFilterChange}
                onRefresh={handleRefresh}

              />
            );
          })()
        )}
      </TabPanel>

      <TabPanel value={tab} index={3}>
        {subscriptionData && (
          <SubscriptionSecurityTab
            subscription={{
              id: subscriptionData.subscription.id,
              ip_whitelist: Array.isArray((subscriptionData.subscription as any).ip_whitelist)
                ? (subscriptionData.subscription as any).ip_whitelist.map((ip: any) => typeof ip === 'string' ? ip : ip.address)
                : [],
              ip_blacklist: Array.isArray((subscriptionData.subscription as any).ip_blacklist)
                ? (subscriptionData.subscription as any).ip_blacklist.map((ip: any) => typeof ip === 'string' ? ip : ip.address)
                : [],
              enforce_ip_restrictions: (subscriptionData.subscription as any).ip_restriction === 'enabled'
            }}
            onUpdateIpWhitelist={handleUpdateIpWhitelist}
            onUpdateIpBlacklist={handleUpdateIpBlacklist}
            onToggleIpRestrictions={handleToggleIpRestrictions}
            isLoading={false}
            isUpdating={updateStatusMutation.isPending}
          />
        )}
      </TabPanel>

      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
        aria-labelledby="delete-dialog-title"
        aria-describedby="delete-dialog-description"
      >
        <DialogTitle id="delete-dialog-title">Delete Subscription</DialogTitle>
        <DialogContent>
          <DialogContentText id="delete-dialog-description">
            Are you sure you want to delete this subscription? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel} color="primary">
            Cancel
          </Button>
          <Button 
            onClick={handleDeleteConfirm} 
            color="error"
            disabled={deleteMutation.isPending}
            startIcon={deleteMutation.isPending ? <CircularProgress size={20} /> : null}
          >
            {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert 
          onClose={() => setSnackbar(prev => ({ ...prev, open: false }))} 
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </PageContainer>
  );
};

export default SubscriptionDetailsPage;