import React from 'react';
import { 
  Box, 
  Typography, 
  Grid, 
  Divider, 
  Button, 
  IconButton, 
  Chip, 
  LinearProgress, 
  useTheme,
  Tooltip,
  Card,
  CardContent,
  CardHeader,
  Avatar,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Badge,
  Skeleton,
  CardActions,
  Link,
  CircularProgress,
  Paper,
} from '@mui/material';
import {
  Person as PersonIcon,
  Dns as NodeIcon,
  Event as EventIcon,
  Speed as SpeedIcon,
  DataUsage as DataUsageIcon,
  CloudQueue as CloudIcon,
  CloudOff as CloudOffIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Edit as EditIcon,
  Refresh as RefreshIcon,
  History as HistoryIcon,
  Security as SecurityIcon,
  Receipt as ReceiptIcon,
  CalendarToday as CalendarIcon,
  Update as UpdateIcon,
  Timer as TimerIcon,
  Storage as StorageIcon,
  NetworkCheck as NetworkCheckIcon,
  Public as PublicIcon,
  VpnKey as VpnKeyIcon,
  Speed as SpeedMeterIcon,
  Link as LinkIcon,
  CopyAll as CopyIcon,
  OpenInNew as OpenInNewIcon,
  ContentCopy as ContentCopyIcon,
} from '@mui/icons-material';
import { formatBytes, formatDate, formatDateTime, formatDuration } from '../../utils/formatters';
import { Subscription, SubscriptionStatus } from '../../types/subscription';
import { User } from '../../types/user';
import { Node } from '../../types/node';

interface SubscriptionOverviewTabProps {
  subscription: Subscription;
  user?: User;
  node?: Node;
  onToggleStatus: () => void;
  onRefresh: () => void;
  isLoading: boolean;
  isUpdating?: boolean;
}

const SubscriptionOverviewTab: React.FC<SubscriptionOverviewTabProps> = ({
  subscription,
  user,
  node,
  onToggleStatus,
  onRefresh,
  isLoading,
  isUpdating = false,
}) => {
  const theme = useTheme();
  const isExpired = subscription.expires_at && new Date(subscription.expires_at) < new Date();
  
  // Calculate usage percentage
  const usagePercentage = subscription.traffic_limit > 0 
    ? Math.min(100, (subscription.traffic_used / subscription.traffic_limit) * 100)
    : 0;
  
  // Get status color and icon
  const getStatusInfo = () => {
    if (isExpired) {
      return {
        color: 'error' as const,
        icon: <ErrorIcon />,
        text: 'Истекла',
      };
    }
    
    switch (subscription.status) {
      case 'active':
        return {
          color: 'success' as const,
          icon: <CheckCircleIcon />,
          text: 'Активна',
        };
      case 'suspended':
        return {
          color: 'warning' as const,
          icon: <WarningIcon />,
          text: 'Приостановлена',
        };
      case 'expired':
        return {
          color: 'error' as const,
          icon: <ErrorIcon />,
          text: 'Истекла',
        };
      case 'pending':
        return {
          color: 'info' as const,
          icon: <UpdateIcon />,
          text: 'Ожидает активации',
        };
      default:
        return {
          color: 'default' as const,
          icon: <CloudOffIcon />,
          text: 'Неактивна',
        };
    }
  };
  
  const statusInfo = getStatusInfo();
  
  const handleCopyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // You might want to add a snackbar notification here
  };

  if (isLoading) {
    return (
      <Box>
        <Skeleton variant="rectangular" height={56} sx={{ mb: 2 }} />
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Skeleton variant="rectangular" height={300} />
          </Grid>
          <Grid item xs={12} md={4}>
            <Skeleton variant="rectangular" height={300} />
          </Grid>
          <Grid item xs={12} md={4}>
            <Skeleton variant="rectangular" height={300} />
          </Grid>
        </Grid>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center">
          <Typography variant="h5" component="h2" sx={{ mr: 2 }}>
            Обзор подписки
          </Typography>
          <Chip
            icon={statusInfo.icon}
            label={statusInfo.text}
            color={statusInfo.color}
            variant="outlined"
            size="small"
          />
        </Box>
        
        <Box>
          <Tooltip title="Обновить данные">
            <IconButton 
              onClick={onRefresh} 
              disabled={isLoading || isUpdating}
              sx={{ mr: 1 }}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            color={subscription.status === 'active' ? 'error' : 'primary'}
            onClick={onToggleStatus}
            disabled={isLoading || isUpdating}
            startIcon={isUpdating ? <CircularProgress size={20} color="inherit" /> : null}
          >
            {subscription.status === 'active' ? 'Приостановить' : 'Активировать'}
          </Button>
        </Box>
      </Box>
      
      <Grid container spacing={3}>
        {/* User Info */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader
              avatar={
                <Avatar sx={{ bgcolor: theme.palette.primary.main }}>
                  <PersonIcon />
                </Avatar>
              }
              title="Информация о пользователе"
              action={
                <Tooltip title="Перейти в профиль">
                  <IconButton 
                    component={Link} 
                    href={`/users/${user?.id}`}
                    target="_blank"
                    rel="noopener"
                  >
                    <OpenInNewIcon />
                  </IconButton>
                </Tooltip>
              }
            />
            <Divider />
            <CardContent>
              {user ? (
                <List dense>
                  <ListItem>
                    <ListItemIcon>
                      <NodeIcon color="action" />
                    </ListItemIcon>
                    <ListItemText 
                      primary={user?.username || 'Неизвестно'} 
                      secondary="Пользователь"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <VpnKeyIcon color="action" />
                    </ListItemIcon>
                    <ListItemText 
                      primary={
                        <Box component="span" sx={{ display: 'flex', alignItems: 'center' }}>
                          {user?.email || 'Неизвестно'}
                          <IconButton 
                            size="small" 
                            onClick={() => user?.email && handleCopyToClipboard(user.email)}
                            sx={{ ml: 0.5, p: 0.5 }}
                          >
                            <CopyIcon fontSize="small" />
                          </IconButton>
                        </Box>
                      } 
                      secondary="Email"
                    />
                    <ListItemSecondaryAction>
                      <Tooltip title="Открыть ноду">
                        <IconButton edge="end" size="small">
                          <ContentCopyIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </ListItemSecondaryAction>
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <CalendarIcon color="action" />
                    </ListItemIcon>
                    <ListItemText 
                      primary={formatDate(user.created_at)} 
                      secondary="Дата регистрации"
                    />
                  </ListItem>
                </List>
              ) : (
                <Typography color="textSecondary" align="center" py={2}>
                  Информация о пользователе не найдена
                </Typography>
              )}
            </CardContent>
          </Card>
          
          {/* Node Info */}
          <Card sx={{ mt: 3 }}>
            <CardHeader
              avatar={
                <Avatar sx={{ bgcolor: theme.palette.info.main }}>
                  <NodeIcon />
                </Avatar>
              }
              title="Назначенная нода"
              subheader={node ? node.name : 'Не назначена'}
            />
            <Divider />
            <CardContent>
              {node ? (
                <List dense>
                  <ListItem>
                    <ListItemIcon>
                      <PublicIcon color="action" />
                    </ListItemIcon>
                    <ListItemText 
                      primary={node.hostname} 
                      secondary="Хост"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <SpeedMeterIcon color="action" />
                    </ListItemIcon>
                    <ListItemText 
                      primary={
                        <Chip 
                          label={statusInfo.text} 
                          size="small" 
                          color={statusInfo.color} 
                          variant="outlined"
                          icon={statusInfo.icon}
                        />
                      } 
                      secondary="Статус"
                    />
                    <ListItemSecondaryAction>
                      <Box sx={{ 
                        width: 10, 
                        height: 10, 
                        borderRadius: '50%', 
                        bgcolor: node.status === 'online' ? 'success.main' : 'error.main',
                        mr: 1,
                      }} />
                    </ListItemSecondaryAction>
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <StorageIcon color="action" />
                    </ListItemIcon>
                    <ListItemText 
                      primary={`${node.city || 'Неизвестно'}, ${node.country || ''}`} 
                      secondary="Расположение"
                    />
                  </ListItem>
                </List>
              ) : (
                <Typography color="textSecondary" align="center" py={2}>
                  Нода не назначена
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
        
        {/* Subscription Details */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardHeader
              avatar={
                <Avatar sx={{ bgcolor: theme.palette.secondary.main }}>
                  <ReceiptIcon />
                </Avatar>
              }
              title="Детали подписки"
              action={
                <Button 
                  size="small" 
                  color="primary" 
                  startIcon={<SecurityIcon />}
                  onClick={() => {
                    // Scroll to security tab and maybe activate it
                    const securityTab = document.getElementById('security-tab');
                    if (securityTab) {
                      securityTab.scrollIntoView({ behavior: 'smooth' });
                      // You might want to add logic to switch to the security tab here
                    }
                  }}
                >
                  Перейти к настройкам
                </Button>
              }
            />
            <Divider />
            <CardContent>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <List dense>
                    <ListItem>
                      <ListItemIcon>
                        <EventIcon color="action" />
                      </ListItemIcon>
                      <ListItemText 
                        primary={
                          <Box>
                            {formatBytes(subscription.traffic_used || 0)}
                            <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                              ({usagePercentage.toFixed(1)}%)
                            </Typography>
                          </Box>
                        } 
                        secondary="Использовано"
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <CalendarIcon color="action" />
                      </ListItemIcon>
                      <ListItemText 
                        primary={
                          subscription.expires_at 
                            ? formatDate(subscription.expires_at) + (isExpired ? ' (Истекла)' : '')
                            : 'Бессрочная'
                        }
                        secondary="Дата истечения"
                        primaryTypographyProps={{
                          color: isExpired ? 'error' : 'inherit',
                        }}
                      />
                      {subscription.expires_at && !isExpired && (
                        <ListItemSecondaryAction>
                          <Chip 
                            size="small" 
                            label={`Осталось: ${formatDuration(
                              (new Date(subscription.expires_at).getTime() - Date.now()) / 1000
                            )}`} 
                            color="info"
                            variant="outlined"
                          />
                        </ListItemSecondaryAction>
                      )}
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <TimerIcon color="action" />
                      </ListItemIcon>
                      <ListItemText 
                        primary={
                          subscription.last_connected_at 
                            ? formatDateTime(subscription.last_connected_at)
                            : 'Никогда'
                        } 
                        secondary="Последнее подключение"
                      />
                    </ListItem>
                  </List>
                </Grid>
                <Grid item xs={12} md={6}>
                  <List dense>
                    <ListItem>
                      <ListItemIcon>
                        <CheckCircleIcon color={subscription.is_active ? 'success' : 'disabled'} />
                      </ListItemIcon>
                      <ListItemText 
                        primary={
                          <Chip 
                            label={subscription.ip_restriction === 'enabled' ? 'Включено' : 'Отключено'} 
                            size="small" 
                            color={subscription.ip_restriction === 'enabled' ? 'success' : 'default'} 
                            variant="outlined"
                          />
                        } 
                        secondary="Ограничение по IP"
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <SecurityIcon color="action" />
                      </ListItemIcon>
                      <ListItemText 
                        primary={
                          <Box>
                            <Box>Белый список: {subscription.ip_whitelist?.length || 0} IP</Box>
                            <Box>Черный список: {subscription.ip_blacklist?.length || 0} IP</Box>
                          </Box>
                        } 
                        secondary="Ограничения доступа"
                      />
                      <ListItemSecondaryAction>
                        <Button 
                          size="small" 
                          color="primary" 
                          startIcon={<SecurityIcon />}
                          onClick={() => window.scrollTo({
                            top: document.getElementById('security-tab')?.offsetTop,
                            behavior: 'smooth'
                          })}
                          disabled={subscription.ip_restriction !== 'enabled'}
                        >
                          Перейти к настройкам
                        </Button>
                        </Box>
                      </ListItemSecondaryAction>
                    </ListItem>
                  </List>
                </Grid>
              </Grid>
              
              {subscription.notes && (
                <Box mt={2}>
                  <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                    Примечания
                  </Typography>
                  <Paper variant="outlined" sx={{ p: 2, backgroundColor: theme.palette.background.default }}>
                    <Typography variant="body2" whiteSpace="pre-wrap">
                      {subscription.notes}
                    </Typography>
                  </Paper>
                </Box>
              )}
            </CardContent>
          </Card>
          
          {/* Data Usage */}
          <Card sx={{ mt: 3 }}>
            <CardHeader
              avatar={
                <Avatar sx={{ bgcolor: theme.palette.info.main }}>
                  <DataUsageIcon />
                </Avatar>
              }
              title="Использование трафика"
              subheader={`${formatBytes(subscription.traffic_used)} / ${subscription.traffic_limit ? formatBytes(subscription.traffic_limit) : 'Безлимит'}`}
            />
            <Divider />
            <CardContent>
              <Box mb={2}>
                <Box display="flex" justifyContent="space-between" mb={0.5}>
                  <Typography variant="body2" color="textSecondary">
                    Использовано
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    {usagePercentage.toFixed(1)}%
                  </Typography>
                </Box>
                <LinearProgress 
                  variant="determinate" 
                  value={usagePercentage}
                  color={
                    usagePercentage > 90 
                      ? 'error' 
                      : usagePercentage > 70 
                        ? 'warning' 
                        : 'primary'
                  }
                  sx={{ height: 10, borderRadius: 5 }}
                />
              </Box>
              
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Box 
                    textAlign="center" 
                    p={2} 
                    bgcolor={theme.palette.primary.light} 
                    borderRadius={1}
                    color="primary.contrastText"
                  >
                    <DataUsageIcon fontSize="large" />
                    <Typography variant="h6" gutterBottom>
                      {formatBytes(subscription.traffic_used)}
                    </Typography>
                    <Typography variant="body2">
                      Использовано
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Box 
                    textAlign="center" 
                    p={2} 
                    bgcolor={theme.palette.grey[200]} 
                    borderRadius={1}
                  >
                    <StorageIcon fontSize="large" color="action" />
                    <Typography variant="h6" gutterBottom>
                      {subscription.traffic_limit 
                        ? formatBytes(subscription.traffic_limit - subscription.traffic_used) 
                        : 'Безлимит'}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Осталось
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default SubscriptionOverviewTab;
