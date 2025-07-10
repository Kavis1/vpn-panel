import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  IconButton,
  Tooltip,
  Chip,
  TextField,
  InputAdornment,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  SelectChangeEvent,
  useTheme,
  LinearProgress,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Grid,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Search as SearchIcon,
  FilterList as FilterListIcon,
  Clear as ClearIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
  Download as DownloadIcon,
  Visibility as VisibilityIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { formatDistanceToNow } from 'date-fns/formatDistanceToNow';
import { ru } from 'date-fns/locale';
import { formatBytes, formatDateTime, formatDistanceToNowSafe } from '../../utils/formatters';

interface LogEntry {
  id: string;
  timestamp: string;
  action: string;
  ip_address: string;
  user_agent?: string;
  location?: {
    country?: string;
    city?: string;
    isp?: string;
  };
  bytes_sent?: number;
  bytes_received?: number;
  duration?: number; // in seconds
  status: 'success' | 'warning' | 'error' | 'info';
  details?: string;
}

interface SubscriptionLogsTabProps {
  logs: LogEntry[];
  totalLogs: number;
  page: number;
  rowsPerPage: number;
  onPageChange: (newPage: number) => void;
  onRowsPerPageChange: (newRowsPerPage: number) => void;
  onRefresh: () => void;
  isLoading: boolean;
  filters: {
    search: string;
    status: string;
    action: string;
  };
  onFilterChange: (filters: {
    search: string;
    status: string;
    action: string;
  }) => void;
}

const SubscriptionLogsTab: React.FC<SubscriptionLogsTabProps> = ({
  logs,
  totalLogs,
  page,
  rowsPerPage,
  onPageChange,
  onRowsPerPageChange,
  onRefresh,
  isLoading,
  filters,
  onFilterChange,
}) => {
  const theme = useTheme();
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null);
  const [openDetails, setOpenDetails] = useState(false);

  const handleChangePage = (event: unknown, newPage: number) => {
    onPageChange(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    onRowsPerPageChange(parseInt(event.target.value, 10));
    onPageChange(0); // Reset to first page when changing rows per page
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange({ ...filters, search: event.target.value });
    onPageChange(0); // Reset to first page when searching
  };

  const handleStatusFilterChange = (event: SelectChangeEvent) => {
    onFilterChange({ ...filters, status: event.target.value });
    onPageChange(0);
  };

  const handleActionFilterChange = (event: SelectChangeEvent) => {
    onFilterChange({ ...filters, action: event.target.value });
    onPageChange(0);
  };

  const clearFilters = () => {
    onFilterChange({ search: '', status: '', action: '' });
  };

  const handleViewDetails = (log: LogEntry) => {
    setSelectedLog(log);
    setOpenDetails(true);
  };

  const handleCloseDetails = () => {
    setOpenDetails(false);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon color="success" fontSize="small" />;
      case 'warning':
        return <WarningIcon color="warning" fontSize="small" />;
      case 'error':
        return <ErrorIcon color="error" fontSize="small" />;
      default:
        return <InfoIcon color="info" fontSize="small" />;
    }
  };

  const getStatusChip = (status: string) => {
    const statusMap: Record<string, { label: string; color: 'success' | 'warning' | 'error' | 'default' }> = {
      success: { label: 'Успешно', color: 'success' },
      warning: { label: 'Предупреждение', color: 'warning' },
      error: { label: 'Ошибка', color: 'error' },
    };

    const statusInfo = statusMap[status] || { label: status, color: 'default' };
    
    return (
      <Chip
        icon={getStatusIcon(status)}
        label={statusInfo.label}
        size="small"
        color={statusInfo.color}
        variant="outlined"
      />
    );
  };

  const getActionLabel = (action: string) => {
    const actionMap: Record<string, string> = {
      connect: 'Подключение',
      disconnect: 'Отключение',
      auth_success: 'Успешная аутентификация',
      auth_failed: 'Ошибка аутентификации',
      limit_reached: 'Достигнут лимит',
      subscription_expired: 'Подписка истекла',
      ip_blocked: 'IP заблокирован',
      device_blocked: 'Устройство заблокировано',
      protocol_error: 'Ошибка протокола',
      rate_limit: 'Превышен лимит запросов',
    };

    return actionMap[action] || action;
  };

  const hasActiveFilters = filters.search || filters.status || filters.action;

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center">
          <Typography variant="h5" component="h2" sx={{ mr: 2 }}>
            История подключений
          </Typography>
          <Tooltip title="Обновить">
            <IconButton onClick={onRefresh} disabled={isLoading} size="small">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
        
        <Box display="flex" alignItems="center">
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            size="small"
            sx={{ mr: 1 }}
            disabled={logs.length === 0 || isLoading}
          >
            Экспорт
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box display="flex" flexWrap="wrap" gap={2} alignItems="center">
          <TextField
            size="small"
            placeholder="Поиск по IP, агенту..."
            variant="outlined"
            value={filters.search}
            onChange={handleSearchChange}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
              endAdornment: filters.search && (
                <InputAdornment position="end">
                  <IconButton size="small" onClick={() => onFilterChange({ ...filters, search: '' })}>
                    <ClearIcon fontSize="small" />
                  </IconButton>
                </InputAdornment>
              ),
            }}
            sx={{ minWidth: 250, flexGrow: 1, maxWidth: 400 }}
          />
          
          <FormControl size="small" sx={{ minWidth: 180 }}>
            <InputLabel id="status-filter-label">Статус</InputLabel>
            <Select
              labelId="status-filter-label"
              id="status-filter"
              value={filters.status}
              onChange={handleStatusFilterChange}
              label="Статус"
            >
              <MenuItem value="">Все статусы</MenuItem>
              <MenuItem value="success">Успешно</MenuItem>
              <MenuItem value="warning">Предупреждение</MenuItem>
              <MenuItem value="error">Ошибка</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel id="action-filter-label">Действие</InputLabel>
            <Select
              labelId="action-filter-label"
              id="action-filter"
              value={filters.action}
              onChange={handleActionFilterChange}
              label="Действие"
            >
              <MenuItem value="">Все действия</MenuItem>
              <MenuItem value="connect">Подключение</MenuItem>
              <MenuItem value="disconnect">Отключение</MenuItem>
              <MenuItem value="auth_success">Успешная аутентификация</MenuItem>
              <MenuItem value="auth_failed">Ошибка аутентификации</MenuItem>
              <MenuItem value="limit_reached">Достигнут лимит</MenuItem>
              <MenuItem value="subscription_expired">Подписка истекла</MenuItem>
              <MenuItem value="ip_blocked">IP заблокирован</MenuItem>
              <MenuItem value="device_blocked">Устройство заблокировано</MenuItem>
              <MenuItem value="protocol_error">Ошибка протокола</MenuItem>
              <MenuItem value="rate_limit">Превышен лимит запросов</MenuItem>
            </Select>
          </FormControl>
          
          {hasActiveFilters && (
            <Button
              size="small"
              startIcon={<ClearIcon />}
              onClick={clearFilters}
              sx={{ ml: 'auto' }}
            >
              Сбросить фильтры
            </Button>
          )}
        </Box>
      </Paper>

      {/* Logs Table */}
      <Paper sx={{ width: '100%', overflow: 'hidden' }}>
        <TableContainer sx={{ maxHeight: 'calc(100vh - 320px)', minHeight: 300 }}>
          {isLoading ? (
            <Box display="flex" justifyContent="center" alignItems="center" p={3}>
              <LinearProgress sx={{ width: '100%' }} />
            </Box>
          ) : logs.length === 0 ? (
            <Box p={3} textAlign="center">
              <Typography variant="body1" color="textSecondary">
                {hasActiveFilters 
                  ? 'Нет записей, соответствующих выбранным фильтрам' 
                  : 'Нет данных о подключениях'}
              </Typography>
              {hasActiveFilters && (
                <Button 
                  variant="text" 
                  size="small" 
                  onClick={clearFilters}
                  sx={{ mt: 1 }}
                >
                  Сбросить фильтры
                </Button>
              )}
            </Box>
          ) : (
            <Table stickyHeader size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Время</TableCell>
                  <TableCell>Статус</TableCell>
                  <TableCell>Действие</TableCell>
                  <TableCell>IP-адрес</TableCell>
                  <TableCell>Местоположение</TableCell>
                  <TableCell>Трафик</TableCell>
                  <TableCell>Длит.</TableCell>
                  <TableCell align="right">Действия</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {logs.map((log) => (
                  <TableRow 
                    key={log.id}
                    hover
                    sx={{ 
                      '&:nth-of-type(odd)': {
                        backgroundColor: theme.palette.action.hover,
                      },
                    }}
                  >
                    <TableCell>
                      <Box display="flex" flexDirection="column">
                        <Typography variant="body2">
                          {format(new Date(log.timestamp), 'dd.MM.yyyy')}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          {format(new Date(log.timestamp), 'HH:mm:ss')}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      {getStatusChip(log.status)}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {getActionLabel(log.action)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontFamily="monospace">
                        {log.ip_address}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {log.location?.country ? (
                        <Box>
                          <Typography variant="body2">
                            {log.location.city ? `${log.location.city}, ` : ''}
                            {log.location.country}
                          </Typography>
                          {log.location.isp && (
                            <Typography variant="caption" color="textSecondary">
                              {log.location.isp}
                            </Typography>
                          )}
                        </Box>
                      ) : (
                        <Typography variant="body2" color="textSecondary">
                          Неизвестно
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      {(log.bytes_sent || log.bytes_received) ? (
                        <Box>
                          <Typography variant="body2">
                            ↑ {formatBytes(log.bytes_sent || 0)}
                          </Typography>
                          <Typography variant="body2">
                            ↓ {formatBytes(log.bytes_received || 0)}
                          </Typography>
                        </Box>
                      ) : (
                        <Typography variant="body2" color="textSecondary">
                          Нет данных
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      {log.duration ? (
                        <Typography variant="body2">
                          {log.duration < 60 
                            ? `${log.duration} сек` 
                            : `${Math.floor(log.duration / 60)} мин ${log.duration % 60} сек`}
                        </Typography>
                      ) : (
                        <Typography variant="body2" color="textSecondary">
                          —
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Подробности">
                        <IconButton 
                          size="small" 
                          onClick={() => handleViewDetails(log)}
                          color="primary"
                        >
                          <VisibilityIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </TableContainer>
        
        {!isLoading && logs.length > 0 && (
          <TablePagination
            rowsPerPageOptions={[10, 25, 50, 100]}
            component="div"
            count={totalLogs}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={(e, newPage) => handleChangePage(e, newPage)}
            onRowsPerPageChange={handleChangeRowsPerPage}
            labelRowsPerPage="Строк на странице:"
            labelDisplayedRows={({ from, to, count }) => 
              `${from}-${to} из ${count !== -1 ? count : `более ${to}`}`
            }
          />
        )}
      </Paper>

      {/* Log Details Dialog */}
      {selectedLog && (
        <Dialog 
          open={openDetails} 
          onClose={handleCloseDetails}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Box display="flex" alignItems="center">
                {getStatusIcon(selectedLog.status)}
                <Box ml={1}>
                  {getActionLabel(selectedLog.action)}
                </Box>
              </Box>
              <IconButton onClick={handleCloseDetails} size="small">
                <CloseIcon />
              </IconButton>
            </Box>
          </DialogTitle>
          <DialogContent dividers>
            <Box mb={2}>
              <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                Время события
              </Typography>
              <Typography variant="body1">
                {formatDateTime(selectedLog.timestamp)}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                {formatDistanceToNow(new Date(selectedLog.timestamp), {
                  addSuffix: true,
                  locale: ru,
                })}
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
              <Box sx={{ flex: '1 1 300px', minWidth: '300px' }}>
                <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                  Соединение
                </Typography>
                <Box mb={2}>
                  <Typography variant="caption" color="textSecondary" display="block">
                    IP-адрес
                  </Typography>
                  <Typography variant="body1" fontFamily="monospace">
                    {selectedLog.ip_address}
                  </Typography>
                </Box>
                
                {selectedLog.location && (
                  <Box mb={2}>
                    <Typography variant="caption" color="textSecondary" display="block">
                      Местоположение
                    </Typography>
                    <Typography variant="body1">
                      {selectedLog.location.city && `${selectedLog.location.city}, `}
                      {selectedLog.location.country || 'Неизвестно'}
                    </Typography>
                    {selectedLog.location.isp && (
                      <Typography variant="body2" color="textSecondary">
                        {selectedLog.location.isp}
                      </Typography>
                    )}
                  </Box>
                )}
                
                {selectedLog.user_agent && (
                  <Box mb={2}>
                    <Typography variant="caption" color="textSecondary" display="block">
                      User Agent
                    </Typography>
                    <Typography variant="body2" fontFamily="monospace">
                      {selectedLog.user_agent}
                    </Typography>
                  </Box>
                )}
              </Box>

              <Box sx={{ flex: '1 1 300px', minWidth: '300px' }}>
                <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                  Статистика
                </Typography>
                
                {(selectedLog.bytes_sent || selectedLog.bytes_received) && (
                  <Box mb={2}>
                    <Typography variant="caption" color="textSecondary" display="block">
                      Трафик
                    </Typography>
                    <Typography variant="body2">
                      ↑ {formatBytes(selectedLog.bytes_sent || 0)} отправлено
                    </Typography>
                    <Typography variant="body2">
                      ↓ {formatBytes(selectedLog.bytes_received || 0)} получено
                    </Typography>
                    <Typography variant="body2">
                      ↕ {formatBytes((selectedLog.bytes_sent || 0) + (selectedLog.bytes_received || 0))} всего
                    </Typography>
                  </Box>
                )}
                
                {selectedLog.duration !== undefined && (
                  <Box mb={2}>
                    <Typography variant="caption" color="textSecondary" display="block">
                      Длительность сеанса
                    </Typography>
                    <Typography variant="body1">
                      {selectedLog.duration < 60 
                        ? `${selectedLog.duration} секунд`
                        : selectedLog.duration < 3600
                          ? `${Math.floor(selectedLog.duration / 60)} минут ${selectedLog.duration % 60} секунд`
                          : `${Math.floor(selectedLog.duration / 3600)} часов ${Math.floor((selectedLog.duration % 3600) / 60)} минут`}
                    </Typography>
                  </Box>
                )}
              </Box>
            </Box>
            
            {selectedLog.details && (
              <Box mt={2} pt={2} borderTop={`1px solid ${theme.palette.divider}`}>
                <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                  Детали
                </Typography>
                <Paper 
                  variant="outlined" 
                  sx={{ 
                    p: 2, 
                    backgroundColor: theme.palette.background.default,
                    fontFamily: 'monospace',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}
                >
                  {selectedLog.details}
                </Paper>
              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDetails} color="primary">
              Закрыть
            </Button>
          </DialogActions>
        </Dialog>
      )}
    </Box>
  );
};

export default SubscriptionLogsTab;
