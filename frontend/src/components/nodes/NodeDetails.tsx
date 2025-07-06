import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  IconButton,
  Divider,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  Button,
  CircularProgress,
  Alert,
  useTheme,
  GridProps,
} from '@mui/material';
import {
  Close as CloseIcon,
  CloudQueue as CloudQueueIcon,
  CloudOff as CloudOffIcon,
  Dns as DnsIcon,
  Speed as SpeedIcon,
  Storage as StorageIcon,
  People as PeopleIcon,
  Public as PublicIcon,
  SettingsEthernet as SettingsEthernetIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { styled, Theme } from '@mui/material/styles';
import Tooltip from '@mui/material/Tooltip';

// NodeStatus type
type NodeStatus = 'online' | 'offline' | 'maintenance';

// Node interface
export interface Node {
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

// NodeConnection interface
export interface NodeConnection {
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

// NodeStats interface
export interface NodeStats {
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
  // Additional stats properties with default values
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
  memory_total: 0,
  disk_used: 0,
  disk_total: 0,
  network_rx: 0,
  total_network_rx: 0,
  network_tx: 0,
  total_network_tx: 0,
};

// Import services
import { 
  getNodeStats,
  getNodeConnections,
  toggleNodeStatus,
} from '../../services/nodeService';

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

interface StatIconProps {
  color?: string;
  theme?: Theme;
}

const StatIcon = styled('div')<StatIconProps>(({ theme, color }) => ({
  width: 48,
  height: 48,
  borderRadius: '50%',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  marginBottom: theme.spacing(1),
  backgroundColor: color ? `${color}15` : theme.palette.primary.light,
  color: color || theme.palette.primary.main,
}));

interface StatusBadgeProps {
  status: NodeStatus;
  theme?: Theme;
}

const StatusBadge = styled('span')<StatusBadgeProps>(({ theme, status }) => ({
  display: 'inline-flex',
  alignItems: 'center',
  padding: '4px 8px',
  borderRadius: 16,
  fontSize: '0.75rem',
  fontWeight: 600,
  backgroundColor: status === 'online' 
    ? theme.palette.success.light 
    : status === 'offline'
    ? theme.palette.error.light
    : theme.palette.warning.light,
  color: status === 'online' 
    ? theme.palette.success.contrastText 
    : status === 'offline'
    ? theme.palette.error.contrastText
    : theme.palette.warning.contrastText,
}));

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
  const [activeTab, setActiveTab] = useState('overview');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const theme = useTheme();
  
    // Helper function to get progress color based on percentage
  const getProgressColor = (value: number) => {
    if (value < 50) return 'success';
    if (value < 80) return 'warning';
    return 'error';
  };
  
  // Grid item component with proper typing for MUI v5
  const GridItem = (props: any) => (
    <Grid item component="div" {...props} />
  );
  
  // Grid container component with proper typing for MUI v5
  const GridContainer = (props: any) => (
    <Grid container spacing={2} component="div" {...props} />
  );
  
  // Fetch node stats with proper typing
  const { 
    data: statsData, 
    isLoading: isLoadingStats, 
    error: statsError,
    refetch: refetchStats
  } = useQuery<NodeStats>({
    queryKey: ['nodeStats', node.id],
    queryFn: async () => {
      const response = await getNodeStats(node.id);
      return { ...defaultNodeStats, ...response?.data };
    },
    enabled: activeTab === 'overview' || activeTab === 'stats',
    refetchInterval: 60000, // Refresh every minute
  });
  
  // Fetch node connections with proper typing
  const { 
    data: connectionsData = [], 
    isLoading: isLoadingConnections, 
    error: connectionsError,
    refetch: refetchConnections
  } = useQuery({
    queryKey: ['nodeConnections', node.id],
    queryFn: async () => {
      const response = await getNodeConnections(node.id);
      // Transform the API response to match our NodeConnection interface
      return (response?.data || []).map((conn: any) => ({
        id: conn.id,
        user_id: conn.user_id,
        node_id: conn.node_id,
        ip_address: conn.ip,
        connected_at: conn.connected_time,
        last_seen: conn.last_seen || new Date().toISOString(),
        transferred_bytes: conn.upload || 0,
        received_bytes: conn.download || 0,
        protocol: conn.protocol || 'unknown',
        user_agent: conn.user_agent
      }));
    },
    enabled: activeTab === 'connections',
    refetchInterval: 30000, // Refresh every 30 seconds
  });
  
  // Use the data with proper fallbacks and type safety
  const stats: NodeStats = statsData || defaultNodeStats;
  const connections: NodeConnection[] = Array.isArray(connectionsData) ? connectionsData : [];
  
  const handleTabChange = (event: React.SyntheticEvent, newValue: string) => {
    setActiveTab(newValue);
  };
  
  const handleRefresh = async () => {
    try {
      setIsLoading(true);
      setError(null);
      await Promise.all([refetchStats(), refetchConnections()]);
      if (onRefresh) onRefresh();
    } catch (err) {
      setError('Не удалось обновить данные ноды');
      console.error('Error refreshing node data:', err);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleToggleStatus = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const newStatus = node.status === 'online' ? 'offline' : 'online';
      
      if (onStatusChange) {
        onStatusChange(node.id, newStatus);
      } else {
        await toggleNodeStatus(node.id, newStatus);
        await refetchStats();
      }
    } catch (err) {
      setError('Не удалось изменить статус ноды');
      console.error('Error toggling node status:', err);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Format bytes to human readable format
  const formatBytes = (bytes: number = 0, decimals = 2) => {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  };
  
  // Calculate percentage
  const calculatePercentage = (value: number, total: number) => {
    return total > 0 ? Math.round((value / total) * 100) : 0;
  };
  
  // Render loading state
  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={200}>
        <CircularProgress />
      </Box>
    );
  }

  // Render error state
  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Paper component="div" sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box component="div" sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box display="flex" alignItems="center">
          {node.status === 'online' ? (
            <CloudQueueIcon color="success" sx={{ mr: 1 }} />
          ) : (
            <CloudOffIcon color="error" sx={{ mr: 1 }} />
          )}
          <Typography variant="h6" component="div">
            {node.name}
          </Typography>
          <StatusBadge status={node.status} sx={{ ml: 2 }}>
            {node.status === 'online' ? 'Онлайн' : 'Оффлайн'}
          </StatusBadge>
        </Box>
        
        <Box>
          <Tooltip title="Обновить данные">
            <IconButton 
              onClick={handleRefresh} 
              disabled={isLoading}
              size="small"
              sx={{ mr: 1 }}
            >
              <RefreshIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          
          {onClose && (
            <Tooltip title="Закрыть">
              <IconButton onClick={onClose} size="small">
                <CloseIcon fontSize="small" />
              </IconButton>
            </Tooltip>
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
          <Tab 
            label="Обзор" 
            value="overview" 
            disabled={isLoading}
          />
          <Tab 
            label="Статистика" 
            value="stats" 
            disabled={isLoading}
          />
          <Tab 
            label="Подключения" 
            value="connections" 
            disabled={isLoading}
          />
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
              Закрыть
            </Button>
          }
        >
          {error}
        </Alert>
      )}
      
      {/* Loading Indicator */}
      {isLoading && (
        <Box sx={{ p: 4, textAlign: 'center' }}>
          <CircularProgress size={24} />
        </Box>
      )}
      
      {/* Content */}
      <Box sx={{ p: 2, flex: 1, overflow: 'auto' }}>
        {activeTab === 'overview' && (
          <GridContainer>
            <GridItem>
              <StatCard>
                <CardContent>
                  <StatIcon color="#4caf50">
                    <PeopleIcon fontSize="large" />
                  </StatIcon>
                  <Typography variant="h6" align="center">
                    {node.current_users || 0} / {node.max_users || '∞'}
                  </Typography>
                  <Typography variant="body2" color="textSecondary" align="center">
                    Пользователи
                  </Typography>
                </CardContent>
              </StatCard>
            </GridItem>
            
            <GridItem>
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
            </GridItem>
            
            <GridItem>
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
            </GridItem>
            
            <GridItem>
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
            </GridItem>
            
            <GridItem xs={12}>
              <Paper sx={{ p: 2, mt: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Network Traffic
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
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
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <Box display="flex" alignItems="center" mb={1}>
                      <SettingsEthernetIcon color="secondary" sx={{ mr: 1 }} />
                      <Typography variant="subtitle2">Outgoing</Typography>
                    </Box>
                    <Typography variant="h6">
                      {formatBytes(stats.network_tx || 0)}/s
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      Total: {formatBytes(stats.total_network_tx || 0)}
                    </Typography>
                  </Grid>
                </Grid>
              </Paper>
            </GridItem>
            
            <GridItem xs={12}>
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
            </GridItem>
          </GridContainer>
        </GridContainer>
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
        <Tab 
          label="Обзор" 
          value="overview" 
          disabled={isLoading}
        />
        <Tab 
          label="Статистика" 
          value="stats" 
          disabled={isLoading}
        />
        <Tab 
          label="Подключения" 
          value="connections" 
          disabled={isLoading}
        />
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
            Закрыть
          </Button>
        }
      >
        {error}
      </Alert>
    )}
    
    {/* Loading Indicator */}
    {isLoading && (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <CircularProgress size={24} />
      </Box>
    )}
    
    {/* Content */}
    <Box sx={{ p: 2, flex: 1, overflow: 'auto' }}>
      {activeTab === 'overview' && (
        <GridContainer>
          <GridItem>
            <StatCard>
              <CardContent>
                <StatIcon color="#4caf50">
                  <PeopleIcon fontSize="large" />
                </StatIcon>
                <Typography variant="h6" align="center">
                  {node.current_users || 0} / {node.max_users || '∞'}
                </Typography>
                <Typography variant="body2" color="textSecondary" align="center">
                  Пользователи
                </Typography>
              </CardContent>
            </StatCard>
          </GridItem>
          
          <GridItem>
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
          </GridItem>
          
          <GridItem>
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
          </GridItem>
          
          <GridItem>
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
          </GridItem>
          
          <GridItem xs={12}>
            <Paper sx={{ p: 2, mt: 2 }}>
              <Typography variant="h6" gutterBottom>
                Network Traffic
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
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
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <Box display="flex" alignItems="center" mb={1}>
                    <SettingsEthernetIcon color="secondary" sx={{ mr: 1 }} />
                    <Typography variant="subtitle2">Outgoing</Typography>
                  </Box>
                  <Typography variant="h6">
                    {formatBytes(stats.network_tx || 0)}/s
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Total: {formatBytes(stats.total_network_tx || 0)}
                  </Typography>
                </Grid>
              </Grid>
            </Paper>
          </GridItem>
          
          <GridItem xs={12}>
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
          </GridItem>
        </GridContainer>
      </GridContainer>
    </Box>
    
    {/* Tabs */}
    <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
      <Tabs 
        value={activeTab} 
        onChange={handleTabChange}
        variant="scrollable"
        scrollButtons="auto"
      >
        <Tab 
          label="Обзор" 
          value="overview" 
          disabled={isLoading}
        />
        <Tab 
          label="Статистика" 
          value="stats" 
          disabled={isLoading}
        />
        <Tab 
          label="Подключения" 
          value="connections" 
          disabled={isLoading}
        />
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
            Закрыть
          </Button>
        }
      >
        {error}
      </Alert>
    )}
    
    {/* Loading Indicator */}
    {isLoading && (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <CircularProgress size={24} />
      </Box>
    )}
    
    {/* Content */}
    <Box sx={{ p: 2, flex: 1, overflow: 'auto' }}>
      {activeTab === 'connections' && (
        <Box>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              Активные подключения
            </Typography>
            <Box>
              <Chip 
                label={`Всего: ${connections.length}`} 
                size="small" 
                color="primary"
                variant="outlined"
                sx={{ mr: 1 }}
              />
              <Button 
                size="small" 
                startIcon={<RefreshIcon />}
                onClick={() => refetchConnections()}
                disabled={isLoadingConnections}
              >
                Обновить
              </Button>
            </Box>
              </Paper>
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
