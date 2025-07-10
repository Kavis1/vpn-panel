import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
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
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  TextField,
  MenuItem,
  FormControlLabel,
  Switch,
  useTheme,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as VisibilityIcon,
  ContentCopy as ContentCopyIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Speed as SpeedIcon,
  CalendarToday as CalendarIcon,
  DataUsage as DataUsageIcon,
  Person as PersonIcon,
  Dns as NodeIcon,
} from '@mui/icons-material';
import { format, addDays, isAfter, isBefore } from 'date-fns';
import { formatDistanceToNowSafe } from '../utils/formatters';
import { styled } from '@mui/material/styles';
import { 
  getSubscriptions, 
  createSubscription, 
  updateSubscription, 
  deleteSubscription,
  renewSubscription,
  toggleSubscriptionStatus,
  Subscription,
  SubscriptionStatus,
  SubscriptionPlan,
} from '../services/subscriptionService';
import { getUsers } from '../services/userService';
import { getNodes } from '../services/nodeService';
import Layout from '../components/Layout';

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

const StatusChip = styled(Chip)<{ status: string }>(({ theme, status }) => ({
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

const SubscriptionsPage: React.FC = () => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [openDialog, setOpenDialog] = useState(false);
  const [openDeleteDialog, setOpenDeleteDialog] = useState(false);
  const [selectedSubscription, setSelectedSubscription] = useState<Subscription | null>(null);
  const [activeTab, setActiveTab] = useState('all');
  const [formData, setFormData] = useState<Partial<Subscription>>({
    user_id: '',
    plan_id: '',
    node_id: '',
    status: 'active',
    data_limit: 10737418240, // 10GB in bytes
    data_used: 0,
    expire_date: format(addDays(new Date(), 30), 'yyyy-MM-dd'),
    auto_renew: false,
    notes: '',
  });
  const [error, setError] = useState('');
  
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const theme = useTheme();
  
  // Fetch data
  const { data: subscriptionsData, isLoading, isError } = useQuery({
    queryKey: ['subscriptions'],
    queryFn: getSubscriptions
  });

  const { data: usersData } = useQuery({
    queryKey: ['users'],
    queryFn: getUsers,
    enabled: openDialog
  });

  const { data: nodesData } = useQuery({
    queryKey: ['nodes'],
    queryFn: getNodes,
    enabled: openDialog
  });
  
  // Define subscription plans
  const subscriptionPlans: SubscriptionPlan[] = [
    { id: 'free', name: 'Бесплатный', price: 0, data_limit: 1073741824, duration_days: 7 },
    { id: 'basic', name: 'Базовый', price: 299, data_limit: 10737418240, duration_days: 30 },
    { id: 'standard', name: 'Стандарт', price: 599, data_limit: 53687091200, duration_days: 30 },
    { id: 'premium', name: 'Премиум', price: 999, data_limit: 107374182400, duration_days: 30 },
    { id: 'unlimited', name: 'Безлимитный', price: 1499, data_limit: 0, duration_days: 30 },
  ];
  
  // Mutations
  const createSubscriptionMutation = useMutation({
    mutationFn: createSubscription,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
      handleCloseDialog();
    },
    onError: (error: any) => {
      setError(error.response?.data?.detail || 'Ошибка при создании подписки');
    },
  });

  const updateSubscriptionMutation = useMutation({
    mutationFn: ({ subscriptionId, subscriptionData }: { subscriptionId: string; subscriptionData: any }) =>
      updateSubscription(subscriptionId, subscriptionData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
      handleCloseDialog();
    },
    onError: (error: any) => {
      setError(error.response?.data?.detail || 'Ошибка при обновлении подписки');
    },
  });

  const deleteSubscriptionMutation = useMutation({
    mutationFn: deleteSubscription,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
      setOpenDeleteDialog(false);
    },
  });

  const renewSubscriptionMutation = useMutation({
    mutationFn: ({ subscriptionId, days }: { subscriptionId: string; days: number }) =>
      renewSubscription(subscriptionId, days),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
    },
  });

  const toggleStatusMutation = useMutation({
    mutationFn: ({ subscriptionId, status }: { subscriptionId: string; status: string }) =>
      toggleSubscriptionStatus(subscriptionId, status as 'active' | 'suspended'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
    },
  });

  // Handlers
  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };
  
  const handleOpenDialog = (subscription: Subscription | null = null) => {
    setSelectedSubscription(subscription);
    if (subscription) {
      setFormData({
        user_id: subscription.user_id,
        plan_id: subscription.plan_id,
        node_id: subscription.node_id,
        status: subscription.status,
        data_limit: subscription.data_limit,
        data_used: subscription.data_used,
        expire_date: subscription.expire_date,
        auto_renew: subscription.auto_renew,
        notes: subscription.notes || '',
      });
    } else {
      setFormData({
        user_id: '',
        plan_id: 'basic',
        node_id: '',
        status: 'active',
        data_limit: 10737418240, // 10GB in bytes
        data_used: 0,
        expire_date: format(addDays(new Date(), 30), 'yyyy-MM-dd'),
        auto_renew: false,
        notes: '',
      });
    }
    setError('');
    setOpenDialog(true);
  };
  
  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedSubscription(null);
    setError('');
  };
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };
  
  const handlePlanChange = (planId: string) => {
    const plan = subscriptionPlans.find(p => p.id === planId);
    if (plan) {
      setFormData(prev => ({
        ...prev,
        plan_id: plan.id,
        data_limit: plan.data_limit,
        expire_date: format(
          addDays(new Date(prev.expire_date || new Date()), plan.duration_days),
          'yyyy-MM-dd'
        ),
      }));
    }
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    try {
      if (selectedSubscription) {
        await updateSubscriptionMutation.mutateAsync({
          subscriptionId: selectedSubscription.id,
          subscriptionData: formData,
        });
      } else {
        await createSubscriptionMutation.mutateAsync(formData as Subscription);
      }
    } catch (error) {
      console.error('Error saving subscription:', error);
    }
  };
  
  const handleDelete = async () => {
    if (selectedSubscription) {
      await deleteSubscriptionMutation.mutateAsync(selectedSubscription.id);
    }
  };
  
  const handleRenew = async (subscriptionId: string, days: number) => {
    await renewSubscriptionMutation.mutateAsync({
      subscriptionId,
      days,
    });
  };
  
  const handleToggleStatus = async (subscriptionId: string, currentStatus: SubscriptionStatus) => {
    await toggleStatusMutation.mutateAsync({
      subscriptionId,
      status: currentStatus === 'active' ? 'suspended' : 'active',
    });
  };
  
  const handleCopyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
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
  
  // Filter subscriptions based on active tab
  const filteredSubscriptions = React.useMemo(() => {
    if (!subscriptionsData?.data) return [];
    
    switch (activeTab) {
      case 'active':
        return subscriptionsData.data.filter(
          (sub: Subscription) => sub.status === 'active' && 
            (!sub.expire_date || isAfter(new Date(sub.expire_date), new Date()))
        );
      case 'expired':
        return subscriptionsData.data.filter(
          (sub: Subscription) => sub.status === 'expired' || 
            (sub.expire_date && isBefore(new Date(sub.expire_date), new Date()))
        );
      case 'suspended':
        return subscriptionsData.data.filter((sub: Subscription) => sub.status === 'suspended');
      default:
        return subscriptionsData.data;
    }
  }, [subscriptionsData, activeTab]);
  
  // Pagination
  const paginatedSubscriptions = React.useMemo(() => {
    return filteredSubscriptions.slice(
      page * rowsPerPage,
      page * rowsPerPage + rowsPerPage
    );
  }, [filteredSubscriptions, page, rowsPerPage]);
  
  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }
  
  if (isError) {
    return (
      <Box textAlign="center" p={3}>
        <Alert severity="error">
          Ошибка при загрузке подписок. Пожалуйста, обновите страницу.
        </Alert>
      </Box>
    );
  }
  
  const subscriptions = subscriptionsData?.data || [];
  const users = usersData?.data || [];
  const nodes = nodesData?.data || [];
  
  return (
    <Layout>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Управление подписками
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Добавить подписку
        </Button>
      </Box>
      
      {/* Stats Cards */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, mb: 3 }}>
        <Box sx={{ flex: '1 1 250px', minWidth: '250px' }}>
          <StatCard>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <div>
                  <Typography variant="h6">
                    {subscriptions.length}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Всего подписок
                  </Typography>
                </div>
                <CheckCircleIcon color="primary" fontSize="large" />
              </Box>
            </CardContent>
          </StatCard>
        </Box>

        <Box sx={{ flex: '1 1 250px', minWidth: '250px' }}>
          <StatCard>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <div>
                  <Typography variant="h6">
                    {subscriptions.filter((sub: Subscription) => 
                      sub.status === 'active' && 
                      (!sub.expire_date || isAfter(new Date(sub.expire_date), new Date()))
                    ).length}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Активные
                  </Typography>
                </div>
                <CheckCircleIcon color="success" fontSize="large" />
              </Box>
            </CardContent>
          </StatCard>
        </Box>

        <Box sx={{ flex: '1 1 250px', minWidth: '250px' }}>
          <StatCard>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <div>
                  <Typography variant="h6">
                    {subscriptions.filter((sub: Subscription) => 
                      sub.status === 'expired' || 
                      (sub.expire_date && isBefore(new Date(sub.expire_date), new Date()))
                    ).length}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Истекшие
                  </Typography>
                </div>
                <ErrorIcon color="error" fontSize="large" />
              </Box>
            </CardContent>
          </StatCard>
        </Box>

        <Box sx={{ flex: '1 1 250px', minWidth: '250px' }}>
          <StatCard>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <div>
                  <Typography variant="h6">
                    {subscriptions.filter((sub: Subscription) => 
                      sub.status === 'suspended'
                    ).length}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Приостановленные
                  </Typography>
                </div>
                <ErrorIcon color="warning" fontSize="large" />
              </Box>
            </CardContent>
          </StatCard>
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
          <Tab label="Все" value="all" />
          <Tab label="Активные" value="active" />
          <Tab label="Истекшие" value="expired" />
          <Tab label="Приостановленные" value="suspended" />
        </Tabs>
      </Paper>
      
      {/* Subscriptions Table */}
      <Paper sx={{ width: '100%', overflow: 'hidden', mb: 2 }}>
        <TableContainer sx={{ maxHeight: 'calc(100vh - 400px)' }}>
          <Table stickyHeader aria-label="subscriptions table" size="small">
            <TableHead>
              <TableRow>
                <TableCell>Пользователь</TableCell>
                <TableCell>Тариф</TableCell>
                <TableCell>Статус</TableCell>
                <TableCell>Трафик</TableCell>
                <TableCell>Дата истечения</TableCell>
                <TableCell>Нода</TableCell>
                <TableCell align="right">Действия</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedSubscriptions.map((subscription: Subscription) => {
                const user = users.find((u: any) => u.id === subscription.user_id);
                const node = nodes.find((n: any) => n.id === subscription.node_id);
                const plan = subscriptionPlans.find(p => p.id === subscription.plan_id);
                const isExpired = subscription.expire_date && 
                  isBefore(new Date(subscription.expire_date), new Date());
                const status = isExpired ? 'expired' : subscription.status;
                
                return (
                  <TableRow 
                    key={subscription.id}
                    hover 
                    sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                  >
                    <TableCell>
                      <Box display="flex" alignItems="center">
                        <PersonIcon color="action" sx={{ mr: 1 }} />
                        <div>
                          <Typography variant="body2">
                            {user?.username || 'Неизвестный пользователь'}
                          </Typography>
                          <Typography variant="caption" color="textSecondary">
                            {user?.email || ''}
                          </Typography>
                        </div>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {plan?.name || 'Неизвестный тариф'}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        {plan?.price ? `${plan.price} ₽/мес` : 'Бесплатно'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <StatusChip 
                        label={
                          status === 'active' ? 'Активна' : 
                          status === 'expired' ? 'Истекла' : 
                          'Приостановлена'
                        } 
                        size="small"
                        status={status}
                      />
                    </TableCell>
                    <TableCell>
                      <Box width={150}>
                        <Typography variant="body2">
                          {formatBytes(subscription.data_used)} / 
                          {subscription.data_limit ? formatBytes(subscription.data_limit) : '∞'}
                        </Typography>
                        <LinearProgress 
                          variant="determinate" 
                          value={
                            subscription.data_limit 
                              ? Math.min(100, (subscription.data_used / subscription.data_limit) * 100)
                              : 0
                          }
                          color={
                            subscription.data_limit && 
                            (subscription.data_used / subscription.data_limit) > 0.9 
                              ? 'error' 
                              : 'primary'
                          }
                          sx={{ mt: 0.5 }}
                        />
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {subscription.expire_date 
                          ? format(new Date(subscription.expire_date), 'dd.MM.yyyy')
                          : 'Бессрочно'}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        {subscription.expire_date && (
                          isExpired 
                            ? `Истекла ${formatDistanceToNowSafe(subscription.expire_date)}`
                            : `Истекает ${formatDistanceToNowSafe(subscription.expire_date)}`
                        )}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box display="flex" alignItems="center">
                        <NodeIcon color="action" sx={{ mr: 1 }} />
                        <Typography variant="body2">
                          {node?.name || 'Любая'}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Просмотреть">
                        <IconButton 
                          size="small"
                          onClick={() => navigate(`/subscriptions/${subscription.id}`)}
                        >
                          <VisibilityIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Обновить">
                        <IconButton 
                          size="small"
                          onClick={() => handleOpenDialog(subscription)}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Продлить">
                        <IconButton 
                          size="small"
                          color="primary"
                          onClick={() => handleRenew(subscription.id, 30)}
                        >
                          <RefreshIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                );
              })}
              
              {paginatedSubscriptions.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                    <Typography variant="body1" color="textSecondary">
                      Подписки не найдены
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={filteredSubscriptions.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          labelRowsPerPage="Строк на странице:"
          labelDisplayedRows={({ from, to, count }) => 
            `${from}-${to} из ${count !== -1 ? count : `больше чем ${to}`}`
          }
        />
      </Paper>
      
      {/* Add/Edit Subscription Dialog */}
      <Dialog 
        open={openDialog} 
        onClose={handleCloseDialog} 
        maxWidth="sm" 
        fullWidth
      >
        <form onSubmit={handleSubmit}>
          <DialogTitle>
            {selectedSubscription ? 'Редактировать подписку' : 'Добавить новую подписку'}
          </DialogTitle>
          
          <DialogContent>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
            
            <TextField
              select
              margin="dense"
              name="user_id"
              label="Пользователь"
              fullWidth
              variant="outlined"
              value={formData.user_id}
              onChange={handleInputChange}
              required
              sx={{ mb: 2 }}
            >
              {users.map((user: any) => (
                <MenuItem key={user.id} value={user.id}>
                  {user.username} ({user.email})
                </MenuItem>
              ))}
            </TextField>
            
            <TextField
              select
              margin="dense"
              name="plan_id"
              label="Тарифный план"
              fullWidth
              variant="outlined"
              value={formData.plan_id}
              onChange={(e) => handlePlanChange(e.target.value)}
              required
              sx={{ mb: 2 }}
            >
              {subscriptionPlans.map((plan) => (
                <MenuItem key={plan.id} value={plan.id}>
                  {plan.name} - {plan.price ? `${plan.price} ₽/мес` : 'Бесплатно'}
                  {plan.data_limit ? `, ${formatBytes(plan.data_limit)}` : ', Безлимит'}
                </MenuItem>
              ))}
            </TextField>
            
            <TextField
              select
              margin="dense"
              name="node_id"
              label="Нода (опционально)"
              fullWidth
              variant="outlined"
              value={formData.node_id || ''}
              onChange={handleInputChange}
              sx={{ mb: 2 }}
            >
              <MenuItem value="">Любая доступная</MenuItem>
              {nodes.map((node: any) => (
                <MenuItem key={node.id} value={node.id}>
                  {node.name} ({node.host}:{node.port})
                </MenuItem>
              ))}
            </TextField>
            
            <TextField
              select
              margin="dense"
              name="status"
              label="Статус"
              fullWidth
              variant="outlined"
              value={formData.status}
              onChange={handleInputChange}
              required
              sx={{ mb: 2 }}
            >
              <MenuItem value="active">Активна</MenuItem>
              <MenuItem value="suspended">Приостановлена</MenuItem>
              <MenuItem value="expired">Истекла</MenuItem>
            </TextField>
            
            <TextField
              margin="dense"
              name="data_limit"
              label="Лимит трафика (в байтах)"
              type="number"
              fullWidth
              variant="outlined"
              value={formData.data_limit || ''}
              onChange={handleInputChange}
              helperText={formData.data_limit ? formatBytes(formData.data_limit) : '0 = безлимит'}
              sx={{ mb: 2 }}
            />
            
            <TextField
              margin="dense"
              name="expire_date"
              label="Дата истечения"
              type="date"
              fullWidth
              variant="outlined"
              value={formData.expire_date || ''}
              onChange={handleInputChange}
              InputLabelProps={{
                shrink: true,
              }}
              sx={{ mb: 2 }}
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={formData.auto_renew || false}
                  onChange={handleInputChange}
                  name="auto_renew"
                  color="primary"
                />
              }
              label="Автопродление"
              sx={{ mb: 2 }}
            />
            
            <TextField
              margin="dense"
              name="notes"
              label="Примечания"
              fullWidth
              variant="outlined"
              multiline
              rows={3}
              value={formData.notes || ''}
              onChange={handleInputChange}
            />
          </DialogContent>
          
          <DialogActions>
            <Button onClick={handleCloseDialog} color="inherit">
              Отмена
            </Button>
            <Button 
              type="submit" 
              color="primary" 
              variant="contained"
              disabled={createSubscriptionMutation.isPending || updateSubscriptionMutation.isPending}
            >
              {(createSubscriptionMutation.isPending || updateSubscriptionMutation.isPending) ? (
                <CircularProgress size={24} />
              ) : selectedSubscription ? (
                'Сохранить изменения'
              ) : (
                'Создать подписку'
              )}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
      
      {/* Delete Confirmation Dialog */}
      <Dialog
        open={openDeleteDialog}
        onClose={() => setOpenDeleteDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Подтверждение удаления</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Вы уверены, что хотите удалить подписку для пользователя {selectedSubscription?.user_id ? 
              users.find((u: any) => u.id === selectedSubscription.user_id)?.username : ''}?
            <br />
            Это действие нельзя отменить.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDeleteDialog(false)} color="inherit">
            Отмена
          </Button>
          <Button 
            onClick={handleDelete} 
            color="error" 
            variant="contained"
            disabled={deleteSubscriptionMutation.isPending}
          >
            {deleteSubscriptionMutation.isPending ? (
              <CircularProgress size={24} />
            ) : (
              'Удалить'
            )}
          </Button>
        </DialogActions>
      </Dialog>
    </Layout>
  );
};

export default SubscriptionsPage;
