import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Typography,
  CircularProgress,
  Button,
  Tabs,
  Tab,
  Alert,
  LinearProgress,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  useTheme,
  Grid,
  CardContent,
  IconButton
} from '@mui/material';
import {
  CloudQueue as CloudQueueIcon,
  CloudOff as CloudOffIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  PowerSettingsNew as PowerSettingsNewIcon,
  People as PeopleIcon,
  Public as PublicIcon,
  SettingsEthernet as SettingsEthernetIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

// Types
type NodeStatus = 'online' | 'offline' | 'maintenance';

interface Node {
  id: string;
  name: string;
  status: NodeStatus;
  host: string;
  ip: string;
  location: string;
  tags: string[];
  created_at: string;
  updated_at: string;
  port?: number;
  api_port?: number;
  country?: string;
  is_public?: boolean;
  current_users?: number;
  max_users?: number;
}

interface NodeConnection {
  id: string;
  user_id: string;
  node_id: string;
  ip_address: string;
  connected_at: string;
  last_seen: string;
  transferred_bytes: number;
  received_bytes: number;
  protocol: string;
  user_agent?: string;
}

interface NodeStats {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_in: number;
  network_out: number;
  active_connections: number;
  total_connections: number;
  uptime: number;
  load_average: number[];
  last_updated: string;
  total_traffic: number;
  cpu_percent: number;
  memory_used: number;
  memory_total: number;
  disk_used: number;
  disk_total: number;
  network_rx: number;
  total_network_rx: number;
  network_tx: number;
  total_network_tx: number;
}

// Default empty stats
const defaultNodeStats: NodeStats = {
  cpu_usage: 0,
  memory_usage: 0,
  disk_usage: 0,
  network_in: 0,
  network_out: 0,
  active_connections: 0,
  total_connections: 0,
  uptime: 0,
  load_average: [0, 0, 0],
  last_updated: new Date().toISOString(),
  total_traffic: 0,
  cpu_percent: 0,
  memory_used: 0,
  memory_total: 1, // Avoid division by zero
  disk_used: 0,
  disk_total: 1, // Avoid division by zero
  network_rx: 0,
  total_network_rx: 0,
  network_tx: 0,
  total_network_tx: 0
};

// Styled Components
const StatIcon = styled('div')(({ theme, color = '#4caf50' }) => ({
  width: 48,
  height: 48,
  borderRadius: '50%',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  margin: '0 auto 12px',
  backgroundColor: theme.palette.mode === 'light' 
    ? `${color}1a` 
    : `${color}33`,
  color: color,
  '& .MuiSvgIcon-root': {
    fontSize: 28,
  },
}));

interface StatusBadgeProps {
  status: NodeStatus;
}

const StatusBadge = styled('span')<StatusBadgeProps>(({ theme, status }) => ({
  display: 'inline-flex',
  alignItems: 'center',
  padding: '4px 8px',
  borderRadius: 12,
  fontSize: '0.75rem',
  fontWeight: 500,
  textTransform: 'uppercase',
  letterSpacing: 0.5,
  backgroundColor: status === 'online' 
    ? theme.palette.success.light 
    : status === 'maintenance' 
      ? theme.palette.warning.light 
      : theme.palette.error.light,
  color: status === 'online' 
    ? theme.palette.success.contrastText 
    : status === 'maintenance' 
      ? theme.palette.warning.contrastText 
      : theme.palette.error.contrastText,
  '& svg': {
    fontSize: '1rem',
    marginRight: 4,
  },
}));

const StatCard = styled(Paper)(({ theme }) => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  transition: 'transform 0.2s, box-shadow 0.2s',
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: theme.shadows[4],
  },
}));

// Helper Functions
const formatBytes = (bytes: number, decimals = 2): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

const calculatePercentage = (value: number, total: number): number => {
  if (total <= 0) return 0;
  return Math.min(100, Math.max(0, (value / total) * 100));
};

const getProgressColor = (value: number): 'primary' | 'secondary' | 'error' => {
  if (value > 90) return 'error';
  if (value > 70) return 'secondary';
  return 'primary';
};

interface NodeDetailsProps {
  node: Node;
  onClose?: () => void;
  onRefresh?: () => void;
  onStatusChange?: (nodeId: string, status: NodeStatus) => void;
}

const NodeDetails: React.FC<NodeDetailsProps> = ({
  node,
  onClose,
  onRefresh,
  onStatusChange,
}) => {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState('overview');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Fetch node stats
  const {
    data: stats,
    isLoading: isLoadingStats,
    refetch: refetchStats,
    isError: isStatsError,
    error: statsError,
  } = useQuery<NodeStats, Error>({
    queryKey: ['nodeStats', node.id],
    queryFn: async () => {
      const response = await fetch(`/api/nodes/${node.id}/stats`);
      if (!response.ok) throw new Error('Failed to fetch node stats');
      return response.json();
    },
    initialData: defaultNodeStats,
    refetchInterval: 10000, // 10 seconds
  });

  // Fetch node connections
  const {
    data: connections = [],
    isLoading: isLoadingConnections,
    refetch: refetchConnections,
    isError: isConnectionsError,
    error: connectionsError,
  } = useQuery<NodeConnection[], Error>({
    queryKey: ['nodeConnections', node.id],
    queryFn: async () => {
      const response = await fetch(`/api/nodes/${node.id}/connections`);
      if (!response.ok) throw new Error('Failed to fetch connections');
      return response.json();
    },
  });

  React.useEffect(() => {
    if (isStatsError && statsError) {
      setError(`Failed to load stats: ${statsError.message}`);
    }
  }, [isStatsError, statsError]);

  React.useEffect(() => {
    if (isConnectionsError && connectionsError) {
      setError(`Failed to load connections: ${connectionsError.message}`);
    }
  }, [isConnectionsError, connectionsError]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: string) => {
    setActiveTab(newValue);
  };

  const handleRefresh = async () => {
    setError(null);
    setIsLoading(true);
    try {
      await Promise.all([refetchStats(), refetchConnections()]);
      if (onRefresh) onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh data');
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleStatus = async () => {
    if (!onStatusChange) return;
    
    const newStatus = node.status === 'online' ? 'offline' : 'online';
    setError(null);
    setIsLoading(true);
    
    try {
      // Replace with actual API call
      const response = await fetch(`/api/nodes/${node.id}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      
      if (!response.ok) throw new Error('Failed to update node status');
      
      onStatusChange(node.id, newStatus);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update status');
    } finally {
      setIsLoading(false);
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={200}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Paper component="div" sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box component="div" sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box display="flex" alignItems="center">
          {node.status === 'online' ? (
            <CloudQueueIcon color="success" sx={{ mr: 1 }} />
          ) : (
            <CloudOffIcon color="error" sx={{ mr: 1 }} />
          )}
          <Typography variant="h5" component="h2">
            {node.name}
          </Typography>
          <StatusBadge status={node.status} sx={{ ml: 2 }}>
            {node.status === 'online' ? 'Online' : node.status === 'offline' ? 'Offline' : 'Maintenance'}
          </StatusBadge>
        </Box>
        <Box>
          <IconButton 
            onClick={handleToggleStatus} 
            disabled={isLoading}
            color={node.status === 'online' ? 'error' : 'primary'}
            title={node.status === 'online' ? 'Take Offline' : 'Bring Online'}
          >
            <PowerSettingsNewIcon />
          </IconButton>
          <IconButton 
            onClick={handleRefresh} 
            disabled={isLoading}
            color="primary"
            title="Refresh"
          >
            <RefreshIcon />
          </IconButton>
          {onClose && (
            <IconButton 
              onClick={onClose} 
              disabled={isLoading}
              title="Close"
            >
              <SettingsIcon />
            </IconButton>
          )}
        </Box>
      </Box>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs 
          value={activeTab} 
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab label="Overview" value="overview" disabled={isLoading} />
          <Tab label="Statistics" value="stats" disabled={isLoading} />
          <Tab label="Connections" value="connections" disabled={isLoading} />
        </Tabs>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert 
          severity="error" 
          sx={{ 
            m: 2, 
            '& .MuiAlert-message': { width: '100%' } 
          }}
          action={
            <Button 
              color="inherit" 
              size="small" 
              onClick={() => setError(null)}
            >
              Dismiss
            </Button>
          }
        >
          {error}
        </Alert>
      )}

      {/* Content */}
      <Box sx={{ p: 2, flex: 1, overflow: 'auto' }}>
        {activeTab === 'overview' && (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', mx: -1.5 }}>
            <Box sx={{ width: { xs: '100%', sm: '50%', md: '33.33%' }, p: 1.5 }}>
              <StatCard>
                <CardContent>
                  <StatIcon color="#4caf50">
                    <PeopleIcon fontSize="large" />
                  </StatIcon>
                  <Typography variant="h6" align="center">
                    {node.current_users || 0} / {node.max_users || '∞'}
                  </Typography>
                  <Typography variant="body2" color="textSecondary" align="center">
                    Active Users
                  </Typography>
                </CardContent>
              </StatCard>
            </Box>

            <Box sx={{ width: { xs: '100%', sm: '50%', md: '33.33%' }, p: 1.5 }}>
              <StatCard>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    CPU Usage
                  </Typography>
                  <Typography variant="h5" component="div">
                    {stats.cpu_percent.toFixed(1)}%
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={stats.cpu_percent} 
                    color={getProgressColor(stats.cpu_percent)}
                    sx={{ mt: 1 }}
                  />
                </CardContent>
              </StatCard>
            </Box>

            <Box sx={{ width: { xs: '100%', sm: '50%', md: '33.33%' }, p: 1.5 }}>
              <StatCard>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Memory Usage
                  </Typography>
                  <Typography variant="h5" component="div">
                    {formatBytes(stats.memory_used)} / {formatBytes(stats.memory_total)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {calculatePercentage(stats.memory_used, stats.memory_total).toFixed(1)}% used
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={calculatePercentage(stats.memory_used, stats.memory_total)} 
                    color={getProgressColor(calculatePercentage(stats.memory_used, stats.memory_total))}
                    sx={{ mt: 1 }}
                  />
                </CardContent>
              </StatCard>
            </Box>

            <Box sx={{ width: { xs: '100%', sm: '50%', md: '33.33%' }, p: 1.5 }}>
              <StatCard>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Disk Usage
                  </Typography>
                  <Typography variant="h5" component="div">
                    {formatBytes(stats.disk_used)} / {formatBytes(stats.disk_total)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {calculatePercentage(stats.disk_used, stats.disk_total).toFixed(1)}% used
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={calculatePercentage(stats.disk_used, stats.disk_total)} 
                    color={getProgressColor(calculatePercentage(stats.disk_used, stats.disk_total))}
                    sx={{ mt: 1 }}
                  />
                </CardContent>
              </StatCard>
            </Box>

            <Box sx={{ width: '100%', p: 1.5 }}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Network Traffic
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', mx: -1.5 }}>
                  <Box sx={{ width: { xs: '100%', sm: '50%' }, p: 1.5 }}>
                    <Box display="flex" alignItems="center" mb={1}>
                      <PublicIcon color="primary" sx={{ mr: 1 }} />
                      <Typography variant="subtitle2">Incoming</Typography>
                    </Box>
                    <Typography variant="h6">
                      {formatBytes(stats.network_rx)}/s
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Total: {formatBytes(stats.total_network_rx)}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ width: { xs: '100%', sm: '50%' }, p: 1.5 }}>
                    <Box display="flex" alignItems="center" mb={1}>
                      <SettingsEthernetIcon color="secondary" sx={{ mr: 1 }} />
                      <Typography variant="subtitle2">Outgoing</Typography>
                    </Box>
                    <Typography variant="h6">
                      {formatBytes(stats.network_tx)}/s
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Total: {formatBytes(stats.total_network_tx)}
                    </Typography>
                  </Box>
                </Box>
              </Paper>
            </Box>

            <Box sx={{ width: '100%', p: 1.5 }}>
              <Paper sx={{ p: 2, mt: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Load Average
                </Typography>
                <Box display="flex" gap={2} flexWrap="wrap">
                  {stats.load_average.map((load, index) => (
                    <Chip 
                      key={index}
                      label={`${load.toFixed(2)} (${index === 0 ? '1m' : index === 1 ? '5m' : '15m'})`}
                      color={load > 1 ? 'error' : 'default'}
                      variant="outlined"
                    />
                  ))}
                </Box>
              </Paper>
            </Box>
          </Box>
        )}

        {activeTab === 'connections' && (
          <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Active Connections
              </Typography>
              <Box>
                <Chip 
                  label={`Total: ${connections.length}`} 
                  size="small" 
                  color="primary"
                  variant="outlined"
                  sx={{ mr: 1 }}
                />
                <Button 
                  size="small" 
                  startIcon={<RefreshIcon />}
                  onClick={handleRefresh}
                  disabled={isLoading}
                >
                  Refresh
                </Button>
              </Box>
            </Box>
            
            {connections.length > 0 ? (
              <TableContainer component={Paper}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>User ID</TableCell>
                      <TableCell>IP Address</TableCell>
                      <TableCell>Protocol</TableCell>
                      <TableCell>Sent</TableCell>
                      <TableCell>Received</TableCell>
                      <TableCell>Connected At</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {connections.map((connection) => (
                      <TableRow key={connection.id}>
                        <TableCell>{connection.user_id || 'Unknown'}</TableCell>
                        <TableCell>{connection.ip_address || 'Unknown'}</TableCell>
                        <TableCell>
                          <Chip 
                            label={connection.protocol || 'Unknown'} 
                            size="small" 
                            color="primary"
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>{formatBytes(connection.transferred_bytes)}</TableCell>
                        <TableCell>{formatBytes(connection.received_bytes)}</TableCell>
                        <TableCell>
                          {new Date(connection.connected_at).toLocaleString()}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Paper sx={{ p: 3, textAlign: 'center' }}>
                <Typography variant="body1" color="textSecondary">
                  No active connections
                </Typography>
              </Paper>
            )}
          </Box>
        )}
      </Box>
    </Paper>
  );
};

export default NodeDetails;
