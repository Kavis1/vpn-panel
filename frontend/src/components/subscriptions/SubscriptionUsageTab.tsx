import React from 'react';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Card,
  CardContent,
  CardHeader,
  Avatar,
  useTheme,
  LinearProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  BarChart as BarChartIcon,
  Timeline as TimelineIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  CloudDownload as DownloadCloudIcon,
  CloudUpload as UploadCloudIcon,
  Speed as SpeedIcon,
  DataUsage as DataUsageIcon,
} from '@mui/icons-material';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { formatBytes } from '../../utils/formatters';

interface UsageDataPoint {
  date: string;
  bytes_used: number;
  bytes_in?: number;
  bytes_out?: number;
}

interface SubscriptionUsageTabProps {
  usageData: UsageDataPoint[];
  timeRange: string;
  onTimeRangeChange: (range: string) => void;
  onRefresh: () => void;
  isLoading: boolean;
  subscription: any; // Replace with your Subscription type
}

const SubscriptionUsageTab: React.FC<SubscriptionUsageTabProps> = ({
  usageData,
  timeRange,
  onTimeRangeChange,
  onRefresh,
  isLoading,
  subscription,
}) => {
  const theme = useTheme();

  const handleTimeRangeChange = (event: SelectChangeEvent) => {
    onTimeRangeChange(event.target.value);
  };

  // Format data for charts
  const formatChartData = () => {
    if (!usageData || usageData.length === 0) return [];
    
    return usageData.map(item => ({
      date: formatDateForDisplay(item.date, timeRange),
      upload: item.bytes_out ? item.bytes_out / (1024 * 1024) : 0, // Convert to MB
      download: item.bytes_in ? item.bytes_in / (1024 * 1024) : 0, // Convert to MB
      total: item.bytes_used / (1024 * 1024), // Convert to MB
    }));
  };

  const chartData = formatChartData();
  const hasSplitTrafficData = usageData.some(item => 'bytes_in' in item && 'bytes_out' in item);

  // Calculate total usage for the period
  const totalUsage = usageData.reduce((sum, item) => sum + item.bytes_used, 0);
  const totalUpload = usageData.reduce((sum, item) => sum + (item.bytes_out || 0), 0);
  const totalDownload = usageData.reduce((sum, item) => sum + (item.bytes_in || 0), 0);

  // Format date for display based on time range
  function formatDateForDisplay(dateString: string, range: string) {
    const date = new Date(dateString);
    
    switch (range) {
      case '24h':
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      case '7days':
      case '30days':
        return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
      case '90days':
        return `Неделя ${Math.ceil((date.getDate()) / 7)}`;
      default:
        return date.toLocaleDateString();
    }
  }

  // Custom tooltip for charts
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <Paper sx={{ p: 2, border: `1px solid ${theme.palette.divider}` }}>
          <Typography variant="subtitle2" gutterBottom>
            {label}
          </Typography>
          {hasSplitTrafficData ? (
            <>
              <Typography variant="body2">
                <strong>Загрузка:</strong> {formatBytes(payload[0].value * 1024 * 1024)}
              </Typography>
              <Typography variant="body2">
                <strong>Скачивание:</strong> {formatBytes(payload[1].value * 1024 * 1024)}
              </Typography>
              <Typography variant="body2">
                <strong>Всего:</strong> {formatBytes(payload[2].value * 1024 * 1024)}
              </Typography>
            </>
          ) : (
            <Typography variant="body2">
              <strong>Использовано:</strong> {formatBytes(payload[0].value * 1024 * 1024)}
            </Typography>
          )}
        </Paper>
      );
    }
    return null;
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center">
          <Typography variant="h5" component="h2" sx={{ mr: 2 }}>
            Статистика использования
          </Typography>
          <Tooltip title="Обновить данные">
            <IconButton onClick={onRefresh} disabled={isLoading} size="small">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
        
        <FormControl variant="outlined" size="small" sx={{ minWidth: 120 }}>
          <InputLabel id="time-range-select-label">Период</InputLabel>
          <Select
            labelId="time-range-select-label"
            id="time-range-select"
            value={timeRange}
            onChange={handleTimeRangeChange}
            label="Период"
            disabled={isLoading}
          >
            <MenuItem value="24h">24 часа</MenuItem>
            <MenuItem value="7days">7 дней</MenuItem>
            <MenuItem value="30days">30 дней</MenuItem>
            <MenuItem value="90days">90 дней</MenuItem>
          </Select>
        </FormControl>
      </Box>
      
      {isLoading ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight={300}>
          <LinearProgress sx={{ width: '100%', maxWidth: 400 }} />
        </Box>
      ) : usageData.length === 0 ? (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="body1" color="textSecondary">
            Нет данных об использовании за выбранный период
          </Typography>
        </Paper>
      ) : (
        <>
          {/* Summary Cards */}
          <Grid container spacing={3} mb={3}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={1}>
                    <DataUsageIcon color="primary" sx={{ mr: 1 }} />
                    <Typography variant="subtitle1" color="textSecondary">
                      Всего использовано
                    </Typography>
                  </Box>
                  <Typography variant="h4">
                    {formatBytes(totalUsage)}
                  </Typography>
                  <Typography variant="body2" color="textSecondary" mt={1}>
                    за {timeRange === '24h' ? 'последние 24 часа' : 
                        timeRange === '7days' ? 'неделю' : 
                        timeRange === '30days' ? 'месяц' : '3 месяца'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            {hasSplitTrafficData && (
              <>
                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Box display="flex" alignItems="center" mb={1}>
                        <DownloadCloudIcon color="primary" sx={{ mr: 1 }} />
                        <Typography variant="subtitle1" color="textSecondary">
                          Скачано
                        </Typography>
                      </Box>
                      <Typography variant="h4">
                        {formatBytes(totalDownload)}
                      </Typography>
                      <Typography variant="body2" color="textSecondary" mt={1}>
                        {totalUsage > 0 ? `${((totalDownload / totalUsage) * 100).toFixed(1)}% от общего трафика` : 'Нет данных'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Box display="flex" alignItems="center" mb={1}>
                        <UploadCloudIcon color="primary" sx={{ mr: 1 }} />
                        <Typography variant="subtitle1" color="textSecondary">
                          Загружено
                        </Typography>
                      </Box>
                      <Typography variant="h4">
                        {formatBytes(totalUpload)}
                      </Typography>
                      <Typography variant="body2" color="textSecondary" mt={1}>
                        {totalUsage > 0 ? `${((totalUpload / totalUsage) * 100).toFixed(1)}% от общего трафика` : 'Нет данных'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </>
            )}
          </Grid>
          
          {/* Charts */}
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Paper sx={{ p: 2 }}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">
                    График использования трафика
                  </Typography>
                  <Box>
                    <Tooltip title="Скачать данные (CSV)">
                      <IconButton size="small" disabled={isLoading}>
                        <DownloadIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>
                <Divider sx={{ mb: 2 }} />
                <Box height={400}>
                  <ResponsiveContainer width="100%" height="100%">
                    {hasSplitTrafficData ? (
                      <LineChart
                        data={chartData}
                        margin={{
                          top: 5,
                          right: 30,
                          left: 20,
                          bottom: 5,
                        }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                        <XAxis 
                          dataKey="date" 
                          tick={{ fontSize: 12 }}
                          tickMargin={10}
                        />
                        <YAxis 
                          tickFormatter={(value) => formatBytes(value * 1024 * 1024, 0).replace(/[^0-9.]/g, '')}
                          tick={{ fontSize: 12 }}
                          tickMargin={10}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend />
                        <Line 
                          type="monotone" 
                          dataKey="download" 
                          name="Скачано" 
                          stroke={theme.palette.success.main} 
                          activeDot={{ r: 6 }} 
                          strokeWidth={2}
                          dot={false}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="upload" 
                          name="Загружено" 
                          stroke={theme.palette.info.main} 
                          activeDot={{ r: 6 }} 
                          strokeWidth={2}
                          dot={false}
                        />
                      </LineChart>
                    ) : (
                      <BarChart
                        data={chartData}
                        margin={{
                          top: 5,
                          right: 30,
                          left: 20,
                          bottom: 5,
                        }}
                        barSize={20}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                        <XAxis 
                          dataKey="date" 
                          tick={{ fontSize: 12 }}
                          tickMargin={10}
                        />
                        <YAxis 
                          tickFormatter={(value) => formatBytes(value * 1024 * 1024, 0).replace(/[^0-9.]/g, '')}
                          tick={{ fontSize: 12 }}
                          tickMargin={10}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend />
                        <Bar 
                          dataKey="total" 
                          name="Использовано" 
                          fill={theme.palette.primary.main} 
                          radius={[4, 4, 0, 0]}
                        />
                      </BarChart>
                    )}
                  </ResponsiveContainer>
                </Box>
              </Paper>
            </Grid>
            
            {/* Additional charts or data can be added here */}
            {hasSplitTrafficData && (
              <Grid item xs={12}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Соотношение входящего и исходящего трафика
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  <Box height={300}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={[
                          { 
                            name: 'Трафик', 
                            download: totalDownload,
                            upload: totalUpload,
                          }
                        ]}
                        layout="vertical"
                        margin={{
                          top: 5,
                          right: 30,
                          left: 20,
                          bottom: 5,
                        }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                        <XAxis 
                          type="number"
                          tickFormatter={(value) => formatBytes(value, 0)}
                        />
                        <YAxis dataKey="name" type="category" scale="band" />
                        <Tooltip 
                          formatter={(value) => [
                            formatBytes(Number(value)),
                            value === totalDownload ? 'Скачано' : 'Загружено'
                          ]}
                        />
                        <Legend />
                        <Bar 
                          dataKey="download" 
                          name="Скачано" 
                          fill={theme.palette.success.main} 
                          radius={[0, 4, 4, 0]}
                        />
                        <Bar 
                          dataKey="upload" 
                          name="Загружено" 
                          fill={theme.palette.info.main} 
                          radius={[0, 4, 4, 0]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </Box>
                </Paper>
              </Grid>
            )}
          </Grid>
        </>
      )}
    </Box>
  );
};

export default SubscriptionUsageTab;
