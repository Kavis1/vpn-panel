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
import { styled } from '@mui/material/styles';
import { 
  Node, 
  NodeStatus,
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

const StatIcon = styled('div')(({ theme, color }) => ({
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

const StatusBadge = styled('span')(({ theme, status }) => ({
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
  
  // Fetch node stats
  const { 
    data: statsData, 
    isLoading: isLoadingStats, 
    refetch: refetchStats 
  } = useQuery(
    ['node-stats', node.id],
    () => getNodeStats(node.id),
    {
      enabled: activeTab === 'overview' || activeTab === 'stats',
      refetchInterval: 60000, // Refresh every minute
    }
  );
  
  // Fetch node connections
  const { 
    data: connectionsData, 
    isLoading: isLoadingConnections, 
    refetch: refetchConnections 
  } = useQuery(
    ['node-connections', node.id],
    () => getNodeConnections(node.id),
    {
      enabled: activeTab === 'connections',
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );
  
  const stats = statsData?.data || {};
  const connections = connectionsData?.data || [];
  
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
  
  return (
    <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box 
        sx={{ 
          p: 2, 
          display: 'flex', 
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: `1px solid ${theme.palette.divider}`
        }}
      >
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
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={4}>
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
            </Grid>
            
            <Grid item xs={12} sm={6} md={4}>
              <StatCard>
                <CardContent>
                  <StatIcon color="#2196f3">
                    <SpeedIcon fontSize="large" />
                  </StatIcon>
                  <Typography variant="h6" align="center">
                    {formatBytes(stats.total_traffic || 0)}
                  </Typography>
                  <Typography variant="body2" color="textSecondary" align="center">
                    Всего трафика
                  </Typography>
                </CardContent>
              </StatCard>
            </Grid>
            
            <Grid item xs={12} sm={6} md={4}>
              <StatCard>
                <CardContent>
                  <StatIcon color="#9c27b0">
                    <DnsIcon fontSize="large" />
                  </StatIcon>
                  <Typography variant="h6" align="center">
                    {node.host}:{node.port}
                  </Typography>
                  <Typography variant="body2" color="textSecondary" align="center">
                    Адрес сервера
                  </Typography>
                </CardContent>
              </StatCard>
            </Grid>
            
            <Grid item xs={12}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Информация о ноде
                </Typography>
                <Divider sx={{ mb: 2 }} />
                
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2">
                      <strong>Расположение:</strong> {node.location || 'Не указано'}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Страна:</strong> {node.country || 'Не указана'}
                    </Typography>
                    <Typography variant="body2">
                      <strong>API порт:</strong> {node.api_port}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2">
                      <strong>Статус:</strong>{' '}
                      <StatusBadge status={node.status}>
                        {node.status === 'online' ? 'Онлайн' : 'Оффлайн'}
                      </StatusBadge>
                    </Typography>
                    <Typography variant="body2">
                      <strong>Публичная:</strong> {node.is_public ? 'Да' : 'Нет'}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Теги:</strong> {node.tags?.join(', ') || 'Нет'}
                    </Typography>
                  </Grid>
                </Grid>
                
                <Box mt={2} display="flex" justifyContent="flex-end">
                  <Button
                    variant="outlined"
                    color={node.status === 'online' ? 'error' : 'success'}
                    onClick={handleToggleStatus}
                    disabled={isLoading}
                    startIcon={
                      node.status === 'online' ? <CloudOffIcon /> : <CloudQueueIcon />
                    }
                  >
                    {node.status === 'online' ? 'Выключить' : 'Включить'}
                  </Button>
                </Box>
              </Paper>
            </Grid>
          </Grid>
        )}
        
        {activeTab === 'stats' && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Использование ресурсов
            </Typography>
            
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid item xs={12} sm={6} md={4}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                    Загрузка CPU
                  </Typography>
                  <Box display="flex" alignItems="center">
                    <Box width="100%" mr={1}>
                      <LinearProgress 
                        variant="determinate" 
                        value={stats.cpu_percent || 0} 
                        color={stats.cpu_percent > 80 ? 'error' : 'primary'}
                      />
                    </Box>
                    <Typography variant="body2" color="textSecondary">
                      {stats.cpu_percent || 0}%
                    </Typography>
                  </Box>
                </Paper>
              </Grid>
              
              <Grid item xs={12} sm={6} md={4}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                    Использование RAM
                  </Typography>
                  <Box display="flex" alignItems="center">
                    <Box width="100%" mr={1}>
                      <LinearProgress 
                        variant="determinate" 
                        value={calculatePercentage(
                          (stats.memory_used || 0), 
                          (stats.memory_total || 1)
                        )} 
                        color={calculatePercentage(
                          (stats.memory_used || 0), 
                          (stats.memory_total || 1)
                        ) > 80 ? 'error' : 'primary'}
                      />
                    </Box>
                    <Typography variant="body2" color="textSecondary">
                      {formatBytes(stats.memory_used || 0)} / {formatBytes(stats.memory_total || 0)}
                    </Typography>
                  </Box>
                </Paper>
              </Grid>
              
              <Grid item xs={12} sm={6} md={4}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                    Использование диска
                  </Typography>
                  <Box display="flex" alignItems="center">
                    <Box width="100%" mr={1}>
                      <LinearProgress 
                        variant="determinate" 
                        value={calculatePercentage(
                          (stats.disk_used || 0), 
                          (stats.disk_total || 1)
                        )} 
                        color={calculatePercentage(
                          (stats.disk_used || 0), 
                          (stats.disk_total || 1)
                        ) > 80 ? 'error' : 'primary'}
                      />
                    </Box>
                    <Typography variant="body2" color="textSecondary">
                      {formatBytes(stats.disk_used || 0)} / {formatBytes(stats.disk_total || 0)}
                    </Typography>
                  </Box>
                </Paper>
              </Grid>
            </Grid>
            
            <Typography variant="h6" gutterBottom>
              Сетевой трафик
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Paper sx={{ p: 2 }}>
                  <Box display="flex" alignItems="center" mb={1}>
                    <PublicIcon color="primary" sx={{ mr: 1 }} />
                    <Typography variant="subtitle2">Входящий трафик</Typography>
                  </Box>
                  <Typography variant="h6">
                    {formatBytes(stats.network_rx || 0)}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Всего: {formatBytes(stats.total_network_rx || 0)}
                  </Typography>
                </Paper>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Paper sx={{ p: 2 }}>
                  <Box display="flex" alignItems="center" mb={1}>
                    <SettingsEthernetIcon color="secondary" sx={{ mr: 1 }} />
                    <Typography variant="subtitle2">Исходящий трафик</Typography>
                  </Box>
                  <Typography variant="h6">
                    {formatBytes(stats.network_tx || 0)}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Всего: {formatBytes(stats.total_network_tx || 0)}
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
          </Box>
        )}
        
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
            </Box>
            
            {connections.length > 0 ? (
              <Paper>
                <Box sx={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr>
                        <th style={{ textAlign: 'left', padding: '12px 16px', borderBottom: `1px solid ${theme.palette.divider}` }}>Пользователь</th>
                        <th style={{ textAlign: 'left', padding: '12px 16px', borderBottom: `1px solid ${theme.palette.divider}` }}>IP</th>
                        <th style={{ textAlign: 'left', padding: '12px 16px', borderBottom: `1px solid ${theme.palette.divider}` }}>Протокол</th>
                        <th style={{ textAlign: 'right', padding: '12px 16px', borderBottom: `1px solid ${theme.palette.divider}` }}>Входящий</th>
                        <th style={{ textAlign: 'right', padding: '12px 16px', borderBottom: `1px solid ${theme.palette.divider}` }}>Исходящий</th>
                        <th style={{ textAlign: 'right', padding: '12px 16px', borderBottom: `1px solid ${theme.palette.divider}` }}>Время</th>
                      </tr>
                    </thead>
                    <tbody>
                      {connections.map((conn, index) => (
                        <tr 
                          key={index}
                          style={{
                            backgroundColor: index % 2 === 0 ? theme.palette.action.hover : 'transparent',
                            transition: 'background-color 0.2s',
                          }}
                        >
                          <td style={{ padding: '12px 16px', borderBottom: `1px solid ${theme.palette.divider}` }}>
                            <Typography variant="body2">
                              {conn.username || 'Неизвестно'}
                            </Typography>
                          </td>
                          <td style={{ padding: '12px 16px', borderBottom: `1px solid ${theme.palette.divider}` }}>
                            <Typography variant="body2">
                              {conn.ip}
                            </Typography>
                          </td>
                          <td style={{ padding: '12px 16px', borderBottom: `1px solid ${theme.palette.divider}` }}>
                            <Chip 
                              label={conn.protocol.toUpperCase()} 
                              size="small" 
                              color="default"
                              variant="outlined"
                            />
                          </td>
                          <td style={{ padding: '12px 16px', textAlign: 'right', borderBottom: `1px solid ${theme.palette.divider}` }}>
                            <Typography variant="body2">
                              {formatBytes(conn.upload)}
                            </Typography>
                          </td>
                          <td style={{ padding: '12px 16px', textAlign: 'right', borderBottom: `1px solid ${theme.palette.divider}` }}>
                            <Typography variant="body2">
                              {formatBytes(conn.download)}
                            </Typography>
                          </td>
                          <td style={{ padding: '12px 16px', textAlign: 'right', borderBottom: `1px solid ${theme.palette.divider}` }}>
                            <Typography variant="body2">
                              {Math.floor(conn.connected_time / 60)} мин. {conn.connected_time % 60} сек.
                            </Typography>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </Box>
              </Paper>
            ) : (
              <Paper sx={{ p: 3, textAlign: 'center' }}>
                <Typography variant="body1" color="textSecondary">
                  Нет активных подключений
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
