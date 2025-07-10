import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Typography,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
  TextField,
  MenuItem,
  CircularProgress,
  Chip,
  Alert,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as VisibilityIcon,
  Block as BlockIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { styled } from '@mui/material/styles';
import { getUsers, createUser, updateUser, deleteUser, toggleUserStatus } from '../services/userService';
import Layout from '../components/Layout';

// Styled components
const StyledTableRow = styled(TableRow)(({ theme }) => ({
  '&:nth-of-type(odd)': {
    backgroundColor: theme.palette.action.hover,
  },
  '&:last-child td, &:last-child th': {
    border: 0,
  },
}));

const StatusChip = styled(Chip)<{ status: string }>(({ theme, status }) => ({
  fontWeight: 'bold',
  backgroundColor: status === 'active'
    ? theme.palette.success.light
    : theme.palette.error.light,
  color: status === 'active'
    ? theme.palette.success.contrastText
    : theme.palette.error.contrastText,
}));

// Types
interface User {
  id: string;
  username: string;
  email: string;
  status: 'active' | 'suspended' | 'expired';
  data_limit?: number;
  data_used?: number;
  expire_date?: string;
  created_at: string;
  is_admin: boolean;
}

const UsersPage: React.FC = () => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [openDialog, setOpenDialog] = useState(false);
  const [openDeleteDialog, setOpenDeleteDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [formData, setFormData] = useState<Partial<User>>({
    username: '',
    email: '',
    status: 'active',
    data_limit: 10737418240, // 10GB in bytes
    expire_date: '',
    is_admin: false,
  });
  const [error, setError] = useState('');
  
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  // Fetch users
  const { data: usersData, isLoading, isError } = useQuery({
    queryKey: ['users'],
    queryFn: getUsers
  });
  
  // Mutations
  const createUserMutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      handleCloseDialog();
    },
    onError: (error: any) => {
      setError(error.response?.data?.detail || 'Ошибка при создании пользователя');
    },
  });
  
  const updateUserMutation = useMutation({
    mutationFn: updateUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      handleCloseDialog();
    },
    onError: (error: any) => {
      setError(error.response?.data?.detail || 'Ошибка при обновлении пользователя');
    },
  });
  
  const deleteUserMutation = useMutation({
    mutationFn: deleteUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setOpenDeleteDialog(false);
    },
  });
  
  const toggleStatusMutation = useMutation({
    mutationFn: toggleUserStatus,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
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
  
  const handleOpenDialog = (user: User | null = null) => {
    setSelectedUser(user);
    if (user) {
      setFormData({
        username: user.username,
        email: user.email,
        status: user.status,
        data_limit: user.data_limit,
        expire_date: user.expire_date || '',
        is_admin: user.is_admin,
      });
    } else {
      setFormData({
        username: '',
        email: '',
        status: 'active',
        data_limit: 10737418240,
        expire_date: '',
        is_admin: false,
      });
    }
    setError('');
    setOpenDialog(true);
  };
  
  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedUser(null);
    setError('');
  };
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    try {
      if (selectedUser) {
        await updateUserMutation.mutateAsync({
          userId: selectedUser.id,
          userData: formData,
        });
      } else {
        await createUserMutation.mutateAsync(formData as any);
      }
    } catch (error) {
      console.error('Error saving user:', error);
    }
  };
  
  const handleDelete = async () => {
    if (selectedUser) {
      await deleteUserMutation.mutateAsync(selectedUser.id);
    }
  };
  
  const handleToggleStatus = async (userId: string, currentStatus: string) => {
    await toggleStatusMutation.mutateAsync({
      userId,
      status: currentStatus === 'active' ? 'suspended' : 'active',
    });
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
          Ошибка при загрузке списка пользователей. Пожалуйста, обновите страницу.
        </Alert>
      </Box>
    );
  }
  
  const users = usersData?.data || [];
  const emptyRows = page > 0 ? Math.max(0, (1 + page) * rowsPerPage - users.length) : 0;

  return (
    <Layout>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Управление пользователями
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Добавить пользователя
        </Button>
      </Box>
      
      <Paper sx={{ width: '100%', overflow: 'hidden', mb: 2 }}>
        <TableContainer sx={{ maxHeight: 600 }}>
          <Table stickyHeader aria-label="users table">
            <TableHead>
              <TableRow>
                <TableCell>Пользователь</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Статус</TableCell>
                <TableCell>Лимит трафика</TableCell>
                <TableCell>Использовано</TableCell>
                <TableCell>Дата истечения</TableCell>
                <TableCell>Дата создания</TableCell>
                <TableCell align="right">Действия</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {users
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((user: User) => (
                  <StyledTableRow key={user.id} hover>
                    <TableCell>
                      <Box display="flex" alignItems="center">
                        {user.is_admin && (
                          <Tooltip title="Администратор">
                            <CheckCircleIcon color="primary" fontSize="small" sx={{ mr: 1 }} />
                          </Tooltip>
                        )}
                        {user.username}
                      </Box>
                    </TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      <StatusChip 
                        label={user.status === 'active' ? 'Активен' : 'Заблокирован'} 
                        size="small"
                        status={user.status}
                      />
                    </TableCell>
                    <TableCell>{user.data_limit ? formatBytes(user.data_limit) : 'Безлимит'}</TableCell>
                    <TableCell>{formatBytes(user.data_used)}</TableCell>
                    <TableCell>
                      {user.expire_date
                        ? format(new Date(user.expire_date), 'dd MMM yyyy')
                        : 'Бессрочно'}
                    </TableCell>
                    <TableCell>
                      {format(new Date(user.created_at), 'dd MMM yyyy')}
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Просмотр">
                        <IconButton onClick={() => navigate(`/users/${user.id}`)} size="small">
                          <VisibilityIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Редактировать">
                        <IconButton onClick={() => handleOpenDialog(user)} size="small">
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title={user.status === 'active' ? 'Заблокировать' : 'Активировать'}>
                        <IconButton 
                          onClick={() => handleToggleStatus(user.id, user.status)}
                          color={user.status === 'active' ? 'error' : 'success'}
                          size="small"
                        >
                          <BlockIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Удалить">
                        <IconButton 
                          onClick={() => {
                            setSelectedUser(user);
                            setOpenDeleteDialog(true);
                          }} 
                          color="error"
                          size="small"
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </StyledTableRow>
                ))}
              
              {emptyRows > 0 && (
                <TableRow style={{ height: 53 * emptyRows }}>
                  <TableCell colSpan={8} />
                </TableRow>
              )}
              
              {users.length === 0 && (
                <TableRow>
                  <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                    <Typography variant="body1" color="textSecondary">
                      Пользователи не найдены
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
          count={users.length}
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
      
      {/* Add/Edit User Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <form onSubmit={handleSubmit}>
          <DialogTitle>
            {selectedUser ? 'Редактировать пользователя' : 'Добавить пользователя'}
          </DialogTitle>
          
          <DialogContent>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
            
            <TextField
              autoFocus
              margin="dense"
              name="username"
              label="Имя пользователя"
              type="text"
              fullWidth
              variant="outlined"
              value={formData.username}
              onChange={handleInputChange}
              required
              disabled={!!selectedUser}
              sx={{ mb: 2 }}
            />
            
            <TextField
              margin="dense"
              name="email"
              label="Email"
              type="email"
              fullWidth
              variant="outlined"
              value={formData.email}
              onChange={handleInputChange}
              required
              sx={{ mb: 2 }}
            />
            
            <TextField
              select
              margin="dense"
              name="status"
              label="Статус"
              fullWidth
              variant="outlined"
              value={formData.status}
              onChange={handleInputChange}
              sx={{ mb: 2 }}
            >
              <MenuItem value="active">Активен</MenuItem>
              <MenuItem value="suspended">Приостановлен</MenuItem>
              <MenuItem value="expired">Истек срок</MenuItem>
            </TextField>
            
            <TextField
              margin="dense"
              name="data_limit"
              label="Лимит трафика (в байтах)"
              type="number"
              fullWidth
              variant="outlined"
              value={formData.data_limit}
              onChange={handleInputChange}
              helperText={formData.data_limit ? formatBytes(formData.data_limit) : ''}
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
            
            <Box display="flex" alignItems="center" mb={2}>
              <input
                type="checkbox"
                id="is_admin"
                name="is_admin"
                checked={formData.is_admin || false}
                onChange={handleInputChange}
                style={{ marginRight: '8px' }}
              />
              <label htmlFor="is_admin">Администратор</label>
            </Box>
          </DialogContent>
          
          <DialogActions>
            <Button onClick={handleCloseDialog} color="inherit">
              Отмена
            </Button>
            <Button 
              type="submit" 
              color="primary" 
              variant="contained"
              disabled={createUserMutation.isPending || updateUserMutation.isPending}
            >
              {(createUserMutation.isPending || updateUserMutation.isPending) ? (
                <CircularProgress size={24} />
              ) : selectedUser ? (
                'Сохранить изменения'
              ) : (
                'Создать пользователя'
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
            Вы уверены, что хотите удалить пользователя <strong>{selectedUser?.username}</strong>? 
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
            disabled={deleteUserMutation.isPending}
          >
            {deleteUserMutation.isPending ? (
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

export default UsersPage;
