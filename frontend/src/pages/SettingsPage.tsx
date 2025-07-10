import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  Tabs,
  Tab
} from '@mui/material';
import Layout from '../components/Layout';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const SettingsPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [settings, setSettings] = useState({
    siteName: 'VPN Panel',
    siteUrl: 'https://vpn-panel.local',
    adminEmail: 'admin@example.com',
    maxUsers: 1000,
    enableRegistration: true,
    enableNotifications: true,
    sessionTimeout: 30,
    backupEnabled: true,
    logLevel: 'INFO'
  });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleSettingChange = (key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSave = () => {
    // TODO: Implement save settings
    console.log('Saving settings:', settings);
  };

  return (
    <Layout>
      <Typography variant="h4" component="h1" gutterBottom>
        Настройки системы
      </Typography>

      <Paper sx={{ width: '100%' }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="settings tabs">
          <Tab label="Общие" />
          <Tab label="Безопасность" />
          <Tab label="Система" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
            <Box sx={{ flex: '1 1 400px', minWidth: '400px' }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Основные настройки
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <TextField
                      label="Название сайта"
                      value={settings.siteName}
                      onChange={(e) => handleSettingChange('siteName', e.target.value)}
                      fullWidth
                    />
                    <TextField
                      label="URL сайта"
                      value={settings.siteUrl}
                      onChange={(e) => handleSettingChange('siteUrl', e.target.value)}
                      fullWidth
                    />
                    <TextField
                      label="Email администратора"
                      value={settings.adminEmail}
                      onChange={(e) => handleSettingChange('adminEmail', e.target.value)}
                      fullWidth
                    />
                    <TextField
                      label="Максимум пользователей"
                      type="number"
                      value={settings.maxUsers}
                      onChange={(e) => handleSettingChange('maxUsers', parseInt(e.target.value))}
                      fullWidth
                    />
                  </Box>
                </CardContent>
              </Card>
            </Box>

            <Box sx={{ flex: '1 1 400px', minWidth: '400px' }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Функции
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.enableRegistration}
                          onChange={(e) => handleSettingChange('enableRegistration', e.target.checked)}
                        />
                      }
                      label="Разрешить регистрацию"
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.enableNotifications}
                          onChange={(e) => handleSettingChange('enableNotifications', e.target.checked)}
                        />
                      }
                      label="Включить уведомления"
                    />
                  </Box>
                </CardContent>
              </Card>
            </Box>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
            <Box sx={{ flex: '1 1 400px', minWidth: '400px' }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Безопасность
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <TextField
                      label="Время сессии (минуты)"
                      type="number"
                      value={settings.sessionTimeout}
                      onChange={(e) => handleSettingChange('sessionTimeout', parseInt(e.target.value))}
                      fullWidth
                    />
                    <Alert severity="info">
                      Пользователи будут автоматически выходить из системы через указанное время бездействия.
                    </Alert>
                  </Box>
                </CardContent>
              </Card>
            </Box>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
            <Box sx={{ flex: '1 1 400px', minWidth: '400px' }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Система
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.backupEnabled}
                          onChange={(e) => handleSettingChange('backupEnabled', e.target.checked)}
                        />
                      }
                      label="Автоматическое резервное копирование"
                    />
                    <TextField
                      label="Уровень логирования"
                      select
                      value={settings.logLevel}
                      onChange={(e) => handleSettingChange('logLevel', e.target.value)}
                      fullWidth
                      SelectProps={{
                        native: true,
                      }}
                    >
                      <option value="DEBUG">DEBUG</option>
                      <option value="INFO">INFO</option>
                      <option value="WARNING">WARNING</option>
                      <option value="ERROR">ERROR</option>
                    </TextField>
                  </Box>
                </CardContent>
              </Card>
            </Box>
          </Box>
        </TabPanel>

        <Divider />
        <Box sx={{ p: 3, display: 'flex', justifyContent: 'flex-end' }}>
          <Button variant="contained" onClick={handleSave}>
            Сохранить настройки
          </Button>
        </Box>
      </Paper>
    </Layout>
  );
};

export default SettingsPage;
