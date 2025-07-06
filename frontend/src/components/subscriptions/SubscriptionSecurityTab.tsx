import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  TextField,
  Button,
  IconButton,
  Chip,
  Divider,
  FormControl,
  FormLabel,
  FormGroup,
  FormControlLabel,
  Switch,
  Tooltip,
  useTheme,
  Alert,
  AlertTitle,
  Card,
  CardContent,
  CardHeader,
  Avatar,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  InputAdornment,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from '@mui/material';
import {
  Security as SecurityIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  VpnKey as VpnKeyIcon,
  Public as PublicIcon,
  Block as BlockIcon,
  Lock as LockIcon,
  LockOpen as LockOpenIcon,
  Edit as EditIcon,
  ContentCopy as ContentCopyIcon,
  HelpOutline as HelpOutlineIcon,
} from '@mui/icons-material';
import { formatDistanceToNow, format } from 'date-fns';
import { ru } from 'date-fns/locale';

interface IpAddress {
  id: string;
  ip: string;
  created_at: string;
  created_by: string;
  notes?: string;
}

interface SubscriptionSecurityTabProps {
  subscription: {
    id: string;
    ip_whitelist: IpAddress[];
    ip_blacklist: IpAddress[];
    enforce_ip_restrictions: boolean;
  };
  onUpdateIpWhitelist: (ips: string[]) => Promise<void>;
  onUpdateIpBlacklist: (ips: string[]) => Promise<void>;
  onToggleIpRestrictions: (enabled: boolean) => Promise<void>;
  isLoading: boolean;
  isUpdating: boolean;
}

const SubscriptionSecurityTab: React.FC<SubscriptionSecurityTabProps> = ({
  subscription,
  onUpdateIpWhitelist,
  onUpdateIpBlacklist,
  onToggleIpRestrictions,
  isLoading,
  isUpdating,
}) => {
  const theme = useTheme();
  const [newIp, setNewIp] = useState('');
  const [activeTab, setActiveTab] = useState<'whitelist' | 'blacklist'>('whitelist');
  const [ipError, setIpError] = useState<string | null>(null);
  const [confirmDialog, setConfirmDialog] = useState<{
    open: boolean;
    title: string;
    message: string;
    onConfirm: () => void;
  }>({
    open: false,
    title: '',
    message: '',
    onConfirm: () => {},
  });
  const [ipNotes, setIpNotes] = useState<Record<string, string>>({});

  // Validate IP address format
  const validateIpAddress = (ip: string): boolean => {
    // Simple IP validation (supports IPv4 and IPv6)
    const ipv4Regex = /^(\d{1,3}\.){3}\d{1,3}(\/\d{1,2})?$/;
    const ipv6Regex = /^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}(\/\d{1,3})?$/;
    
    // Check if it's a valid IP or CIDR
    if (ipv4Regex.test(ip) || ipv6Regex.test(ip)) {
      // Additional validation for IPv4 octets
      if (ip.includes('.')) {
        const parts = ip.split('/')[0].split('.').map(Number);
        if (parts.some(octet => octet > 255)) {
          return false;
        }
        
        // Validate CIDR if present
        if (ip.includes('/')) {
          const cidr = parseInt(ip.split('/')[1], 10);
          if (isNaN(cidr) || cidr < 0 || cidr > 32) {
            return false;
          }
        }
      }
      
      // Additional validation for IPv6 CIDR
      if (ip.includes(':') && ip.includes('/')) {
        const cidr = parseInt(ip.split('/')[1], 10);
        if (isNaN(cidr) || cidr < 0 || cidr > 128) {
          return false;
        }
      }
      
      return true;
    }
    
    return false;
  };

  const handleAddIp = () => {
    const trimmedIp = newIp.trim();
    
    if (!trimmedIp) {
      setIpError('Введите IP-адрес');
      return;
    }
    
    if (!validateIpAddress(trimmedIp)) {
      setIpError('Неверный формат IP-адреса или CIDR');
      return;
    }
    
    const currentList = activeTab === 'whitelist' 
      ? [...subscription.ip_whitelist] 
      : [...subscription.ip_blacklist];
    
    if (currentList.some(ip => ip.ip === trimmedIp)) {
      setIpError('Этот IP-адрес уже добавлен');
      return;
    }
    
    // Add the new IP to the appropriate list
    const newIpEntry: IpAddress = {
      id: `temp-${Date.now()}`,
      ip: trimmedIp,
      created_at: new Date().toISOString(),
      created_by: 'current_user', // This would be replaced with actual user ID
      notes: ipNotes[trimmedIp] || '',
    };
    
    const updatedList = [...currentList, newIpEntry];
    
    // Call the appropriate update handler
    const updateHandler = activeTab === 'whitelist' 
      ? onUpdateIpWhitelist 
      : onUpdateIpBlacklist;
    
    updateHandler(updatedList.map(item => item.ip))
      .then(() => {
        setNewIp('');
        setIpError(null);
        // Clear the note for this IP
        const newIpNotes = { ...ipNotes };
        delete newIpNotes[trimmedIp];
        setIpNotes(newIpNotes);
      })
      .catch(error => {
        console.error('Error updating IP list:', error);
        setIpError('Ошибка при обновлении списка IP');
      });
  };

  const handleRemoveIp = (ipToRemove: string) => {
    setConfirmDialog({
      open: true,
      title: 'Подтверждение удаления',
      message: `Вы уверены, что хотите удалить IP-адрес ${ipToRemove} из ${activeTab === 'whitelist' ? 'белого' : 'черного'} списка?`,
      onConfirm: () => {
        const currentList = activeTab === 'whitelist' 
          ? [...subscription.ip_whitelist] 
          : [...subscription.ip_blacklist];
        
        const updatedList = currentList.filter(ip => ip.ip !== ipToRemove);
        
        const updateHandler = activeTab === 'whitelist' 
          ? onUpdateIpWhitelist 
          : onUpdateIpBlacklist;
        
        updateHandler(updatedList.map(item => item.ip))
          .catch(error => {
            console.error('Error updating IP list:', error);
          });
        
        setConfirmDialog(prev => ({ ...prev, open: false }));
      },
    });
  };

  const handleToggleIpRestrictions = (event: React.ChangeEvent<HTMLInputElement>) => {
    const enabled = event.target.checked;
    
    if (!enabled && (subscription.ip_whitelist.length > 0 || subscription.ip_blacklist.length > 0)) {
      setConfirmDialog({
        open: true,
        title: 'Отключение ограничений по IP',
        message: 'При отключении ограничений по IP все настройки белого и черного списков будут сохранены, но не будут применяться. Вы уверены, что хотите продолжить?',
        onConfirm: () => {
          onToggleIpRestrictions(enabled)
            .catch(error => {
              console.error('Error toggling IP restrictions:', error);
            });
          setConfirmDialog(prev => ({ ...prev, open: false }));
        },
      });
    } else {
      onToggleIpRestrictions(enabled)
        .catch(error => {
          console.error('Error toggling IP restrictions:', error);
        });
    }
  };

  const handleClearAllIps = () => {
    setConfirmDialog({
      open: true,
      title: 'Очистка списка IP',
      message: `Вы уверены, что хотите удалить все IP-адреса из ${activeTab === 'whitelist' ? 'белого' : 'черного'} списка? Это действие нельзя отменить.`,
      onConfirm: () => {
        const updateHandler = activeTab === 'whitelist' 
          ? onUpdateIpWhitelist 
          : onUpdateIpBlacklist;
        
        updateHandler([])
          .catch(error => {
            console.error('Error clearing IP list:', error);
          });
        
        setConfirmDialog(prev => ({ ...prev, open: false }));
      },
    });
  };

  const handleCopyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // You might want to show a snackbar or tooltip here to indicate successful copy
  };

  const currentList = activeTab === 'whitelist' 
    ? subscription.ip_whitelist 
    : subscription.ip_blacklist;

  const sortedList = [...currentList].sort((a, b) => 
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center">
          <SecurityIcon color="primary" sx={{ mr: 1 }} />
          <Typography variant="h5" component="h2">
            Настройки безопасности
          </Typography>
        </Box>
      </Box>

      {/* IP Restrictions Toggle */}
      <Card sx={{ mb: 3 }}>
        <CardHeader
          avatar={
            <Avatar sx={{ bgcolor: subscription.enforce_ip_restrictions ? theme.palette.success.main : theme.palette.grey[400] }}>
              {subscription.enforce_ip_restrictions ? <LockIcon /> : <LockOpenIcon />}
            </Avatar>
          }
          title={
            <Box display="flex" alignItems="center">
              <Typography variant="h6">
                Ограничения по IP
              </Typography>
              <Tooltip 
                title={
                  <>
                    <Typography variant="body2">
                      <strong>Белый список:</strong> Разрешает доступ только с указанных IP-адресов
                    </Typography>
                    <Typography variant="body2" mt={1}>
                      <strong>Черный список:</strong> Блокирует доступ с указанных IP-адресов
                    </Typography>
                  </>
                }
                arrow
                placement="top"
              >
                <IconButton size="small" sx={{ ml: 1 }}>
                  <HelpOutlineIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
          }
          action={
            <FormControlLabel
              control={
                <Switch
                  checked={subscription.enforce_ip_restrictions}
                  onChange={handleToggleIpRestrictions}
                  color="primary"
                  disabled={isUpdating}
                />
              }
              label={subscription.enforce_ip_restrictions ? 'Включено' : 'Отключено'}
              labelPlacement="start"
              sx={{ mr: 1 }}
            />
          }
        />
        <Divider />
        <CardContent>
          <Typography variant="body1" paragraph>
            {subscription.enforce_ip_restrictions
              ? 'Ограничения по IP активны. Вы можете управлять белым и черным списками IP-адресов ниже.'
              : 'Ограничения по IP отключены. Все IP-адреса будут разрешены, но настройки сохранятся.'}
          </Typography>
          
          {subscription.enforce_ip_restrictions && (
            <Alert 
              severity="info" 
              icon={<InfoIcon fontSize="inherit" />}
              sx={{ mb: 2 }}
            >
              <AlertTitle>Как это работает</AlertTitle>
              <Typography variant="body2">
                {activeTab === 'whitelist' 
                  ? 'Только IP-адреса из белого списка смогут получить доступ к VPN. Все остальные подключения будут заблокированы.'
                  : 'IP-адреса из черного списка будут заблокированы. Все остальные IP-адреса смогут подключаться, если не ограничены другими правилами.'}
              </Typography>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* IP Management Tabs */}
      <Paper sx={{ mb: 3, overflow: 'hidden' }}>
        <Box display="flex" borderBottom={1} borderColor="divider">
          <Box
            sx={{
              px: 3,
              py: 1.5,
              borderBottom: activeTab === 'whitelist' ? `3px solid ${theme.palette.primary.main}` : 'none',
              cursor: 'pointer',
              fontWeight: activeTab === 'whitelist' ? 'bold' : 'normal',
              color: activeTab === 'whitelist' ? 'primary.main' : 'text.secondary',
              '&:hover': {
                backgroundColor: theme.palette.action.hover,
              },
            }}
            onClick={() => setActiveTab('whitelist')}
          >
            <Box display="flex" alignItems="center">
              <CheckCircleIcon fontSize="small" sx={{ mr: 1 }} />
              <Typography variant="subtitle1">
                Белый список
              </Typography>
              <Chip 
                label={subscription.ip_whitelist.length} 
                size="small" 
                sx={{ ml: 1, bgcolor: activeTab === 'whitelist' ? 'primary.light' : 'default' }}
              />
            </Box>
          </Box>
          
          <Box
            sx={{
              px: 3,
              py: 1.5,
              borderBottom: activeTab === 'blacklist' ? `3px solid ${theme.palette.primary.main}` : 'none',
              cursor: 'pointer',
              fontWeight: activeTab === 'blacklist' ? 'bold' : 'normal',
              color: activeTab === 'blacklist' ? 'primary.main' : 'text.secondary',
              '&:hover': {
                backgroundColor: theme.palette.action.hover,
              },
            }}
            onClick={() => setActiveTab('blacklist')}
          >
            <Box display="flex" alignItems="center">
              <BlockIcon fontSize="small" sx={{ mr: 1 }} />
              <Typography variant="subtitle1">
                Черный список
              </Typography>
              <Chip 
                label={subscription.ip_blacklist.length} 
                size="small" 
                sx={{ ml: 1, bgcolor: activeTab === 'blacklist' ? 'primary.light' : 'default' }}
              />
            </Box>
          </Box>
          
          <Box flexGrow={1} />
          
          <Box sx={{ p: 1, display: 'flex', alignItems: 'center' }}>
            <Tooltip title="Обновить">
              <IconButton size="small" onClick={() => window.location.reload()} disabled={isLoading}>
                <RefreshIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
        
        <Box p={3}>
          {/* Add IP Form */}
          <Paper variant="outlined" sx={{ p: 2, mb: 3, backgroundColor: theme.palette.background.default }}>
            <Typography variant="subtitle2" gutterBottom>
              Добавить IP-адрес в {activeTab === 'whitelist' ? 'белый' : 'черный'} список
            </Typography>
            
            <Box display="flex" alignItems="flex-start" gap={2}>
              <Box flexGrow={1}>
                <TextField
                  fullWidth
                  size="small"
                  variant="outlined"
                  placeholder="Введите IP-адрес или CIDR (например, 192.168.1.1 или 192.168.1.0/24)"
                  value={newIp}
                  onChange={(e) => {
                    setNewIp(e.target.value);
                    if (ipError) setIpError(null);
                  }}
                  error={!!ipError}
                  helperText={ipError || 'Поддерживаются IPv4 и IPv6 адреса, включая CIDR нотацию'}
                  disabled={isUpdating || !subscription.enforce_ip_restrictions}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <PublicIcon color={ipError ? 'error' : 'action'} />
                      </InputAdornment>
                    ),
                  }}
                />
                
                {activeTab === 'whitelist' && (
                  <TextField
                    fullWidth
                    size="small"
                    variant="outlined"
                    placeholder="Примечание (необязательно)"
                    value={ipNotes[newIp] || ''}
                    onChange={(e) => setIpNotes(prev => ({
                      ...prev,
                      [newIp]: e.target.value
                    }))}
                    disabled={isUpdating || !subscription.enforce_ip_restrictions}
                    sx={{ mt: 1 }}
                  />
                )}
              </Box>
              
              <Button
                variant="contained"
                color="primary"
                startIcon={<AddIcon />}
                onClick={handleAddIp}
                disabled={isUpdating || !subscription.enforce_ip_restrictions || !newIp.trim()}
                sx={{ height: 40, mt: 0.5 }}
              >
                Добавить
              </Button>
            </Box>
            
            {!subscription.enforce_ip_restrictions && (
              <Alert severity="warning" sx={{ mt: 2 }}>
                Включите ограничения по IP, чтобы добавлять адреса в списки.
              </Alert>
            )}
          </Paper>
          
          {/* IP List */}
          <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="subtitle1">
                {activeTab === 'whitelist' ? 'Разрешенные IP-адреса' : 'Заблокированные IP-адреса'}
                <Typography component="span" color="textSecondary" sx={{ ml: 1 }}>
                  ({currentList.length} {currentList.length % 10 === 1 && currentList.length !== 11 ? 'адрес' : 
                    [2, 3, 4].includes(currentList.length % 10) && ![12, 13, 14].includes(currentList.length) ? 'адреса' : 'адресов'})
                </Typography>
              </Typography>
              
              {currentList.length > 0 && (
                <Button
                  variant="outlined"
                  color="error"
                  size="small"
                  onClick={handleClearAllIps}
                  disabled={isUpdating || !subscription.enforce_ip_restrictions}
                  startIcon={<DeleteIcon />}
                >
                  Очистить все
                </Button>
              )}
            </Box>
            
            {currentList.length === 0 ? (
              <Paper variant="outlined" sx={{ p: 3, textAlign: 'center' }}>
                <Box color="text.secondary" mb={1}>
                  <PublicIcon fontSize="large" />
                </Box>
                <Typography variant="body1" color="textSecondary">
                  {activeTab === 'whitelist' 
                    ? 'Нет IP-адресов в белом списке. Добавьте IP-адреса, чтобы разрешить доступ только с них.'
                    : 'Нет IP-адресов в черном списке. Добавьте IP-адреса, чтобы заблокировать к ним доступ.'}
                </Typography>
              </Paper>
            ) : (
              <Paper variant="outlined">
                <List dense>
                  {sortedList.map((ipEntry) => (
                    <React.Fragment key={ipEntry.id}>
                      <ListItem>
                        <ListItemIcon>
                          <PublicIcon color="action" />
                        </ListItemIcon>
                        <ListItemText
                          primary={
                            <Box display="flex" alignItems="center">
                              <Typography 
                                variant="body1" 
                                component="span" 
                                fontFamily="monospace"
                                sx={{ mr: 1 }}
                              >
                                {ipEntry.ip}
                              </Typography>
                              
                              {ipEntry.ip.includes('/') && (
                                <Chip 
                                  label={
                                    ipEntry.ip.endsWith('/32') || ipEntry.ip.endsWith('/128')
                                      ? 'Один IP'
                                      : ipEntry.ip.endsWith('/24') || ipEntry.ip.endsWith('/64')
                                        ? 'Подсеть'
                                        : 'CIDR'
                                  }
                                  size="small"
                                  variant="outlined"
                                  color="info"
                                />
                              )}
                              
                              {ipEntry.notes && (
                                <Tooltip title={ipEntry.notes} arrow>
                                  <InfoIcon color="action" fontSize="small" sx={{ ml: 1 }} />
                                </Tooltip>
                              )}
                            </Box>
                          }
                          secondary={
                            <Typography variant="caption" color="textSecondary">
                              Добавлено {formatDistanceToNow(new Date(ipEntry.created_at), { 
                                addSuffix: true,
                                locale: ru,
                              })}
                              {ipEntry.created_by && ` • ${ipEntry.created_by}`}
                            </Typography>
                          }
                        />
                        <ListItemSecondaryAction>
                          <Box display="flex" alignItems="center">
                            <Tooltip title="Копировать">
                              <IconButton 
                                size="small" 
                                onClick={() => handleCopyToClipboard(ipEntry.ip)}
                                sx={{ mr: 0.5 }}
                              >
                                <ContentCopyIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            
                            <Tooltip title="Удалить">
                              <IconButton 
                                edge="end" 
                                size="small" 
                                onClick={() => handleRemoveIp(ipEntry.ip)}
                                disabled={isUpdating || !subscription.enforce_ip_restrictions}
                                color="error"
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </ListItemSecondaryAction>
                      </ListItem>
                      <Divider component="li" />
                    </React.Fragment>
                  ))}
                </List>
                
                {isUpdating && (
                  <Box p={2}>
                    <LinearProgress />
                  </Box>
                )}
              </Paper>
            )}
            
            {currentList.length > 0 && (
              <Box mt={1}>
                <Typography variant="caption" color="textSecondary">
                  {activeTab === 'whitelist' 
                    ? 'Только эти IP-адреса смогут подключаться к VPN.'
                    : 'Эти IP-адреса будут заблокированы при попытке подключения.'}
                </Typography>
              </Box>
            )}
          </Box>
        </Box>
      </Paper>
      
      {/* Security Recommendations */}
      <Card>
        <CardHeader
          title={
            <Box display="flex" alignItems="center">
              <SecurityIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6">Рекомендации по безопасности</Typography>
            </Box>
          }
        />
        <Divider />
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Box display="flex" mb={2}>
                <Box mr={2}>
                  {subscription.ip_whitelist.length > 0 ? (
                    <CheckCircleIcon color="success" />
                  ) : (
                    <WarningIcon color="warning" />
                  )}
                </Box>
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Используйте белый список IP
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    {subscription.ip_whitelist.length > 0
                      ? 'Отлично! Вы используете белый список для ограничения доступа.'
                      : 'Рекомендуется настроить белый список IP-адресов, чтобы ограничить доступ к VPN только доверенным адресам.'}
                  </Typography>
                </Box>
              </Box>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Box display="flex" mb={2}>
                <Box mr={2}>
                  {subscription.ip_blacklist.length > 0 ? (
                    <CheckCircleIcon color="success" />
                  ) : (
                    <InfoIcon color="info" />
                  )}
                </Box>
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Блокируйте подозрительные IP
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    {subscription.ip_blacklist.length > 0
                      ? 'Вы уже блокируете подозрительные IP-адреса.'
                      : 'Добавляйте в черный список IP-адреса, с которых были попытки несанкционированного доступа.'}
                  </Typography>
                </Box>
              </Box>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Box display="flex">
                <Box mr={2}>
                  {subscription.enforce_ip_restrictions ? (
                    <CheckCircleIcon color="success" />
                  ) : (
                    <ErrorIcon color="error" />
                  )}
                </Box>
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Включите ограничения по IP
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    {subscription.enforce_ip_restrictions
                      ? 'Ограничения по IP включены. Ваши настройки безопасности активны.'
                      : 'Ограничения по IP отключены. Включите их для применения настроек безопасности.'}
                  </Typography>
                </Box>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
      
      {/* Confirm Dialog */}
      <Dialog
        open={confirmDialog.open}
        onClose={() => setConfirmDialog(prev => ({ ...prev, open: false }))}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>{confirmDialog.title}</DialogTitle>
        <DialogContent>
          <DialogContentText>
            {confirmDialog.message}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setConfirmDialog(prev => ({ ...prev, open: false }))}
            color="primary"
          >
            Отмена
          </Button>
          <Button 
            onClick={() => {
              confirmDialog.onConfirm();
            }}
            color="primary"
            variant="contained"
            autoFocus
          >
            Подтвердить
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SubscriptionSecurityTab;
