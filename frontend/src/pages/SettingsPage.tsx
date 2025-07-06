import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const SettingsPage: React.FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Настройки
        </Typography>
        <Typography variant="body1">
          Этот раздел находится в разработке. Здесь будут находиться настройки приложения.
        </Typography>
      </Paper>
    </Box>
  );
};

export default SettingsPage;
