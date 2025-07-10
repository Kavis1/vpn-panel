import React from 'react';
import { Alert, AlertTitle, Button, Box } from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';

interface ErrorAlertProps {
  message: string;
  onRetry?: () => void;
  severity?: 'error' | 'warning' | 'info' | 'success';
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  message,
  onRetry,
  severity = 'error',
}) => {
  return (
    <Box sx={{ width: '100%', maxWidth: 800, mx: 'auto', my: 4 }}>
      <Alert
        severity={severity}
        action={
          onRetry && (
            <Button
              color="inherit"
              size="small"
              onClick={onRetry}
              startIcon={<RefreshIcon />}
            >
              Повторить
            </Button>
          )
        }
      >
        <AlertTitle>
          {severity === 'error' && 'Ошибка'}
          {severity === 'warning' && 'Предупреждение'}
          {severity === 'info' && 'Информация'}
          {severity === 'success' && 'Успех'}
        </AlertTitle>
        {message}
      </Alert>
    </Box>
  );
};

export default ErrorAlert;
