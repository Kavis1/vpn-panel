/**
 * Utility types and helpers for styled components
 */
import { Theme } from '@mui/material/styles';

/**
 * Helper type for styled component props with custom properties
 */
export interface StyledProps<T = {}> {
  theme: Theme;
}

/**
 * Helper type for status-based styled components
 */
export interface StatusStyledProps extends StyledProps {
  status: string;
}

/**
 * Helper function to create status-based styles
 */
export const createStatusStyles = (theme: Theme, status: string) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
      case 'online':
      case 'success':
        return {
          backgroundColor: theme.palette.success.light,
          color: theme.palette.success.contrastText,
        };
      case 'inactive':
      case 'offline':
      case 'suspended':
      case 'error':
        return {
          backgroundColor: theme.palette.error.light,
          color: theme.palette.error.contrastText,
        };
      case 'warning':
      case 'expired':
        return {
          backgroundColor: theme.palette.warning.light,
          color: theme.palette.warning.contrastText,
        };
      case 'info':
      case 'pending':
        return {
          backgroundColor: theme.palette.info.light,
          color: theme.palette.info.contrastText,
        };
      default:
        return {
          backgroundColor: theme.palette.grey[300],
          color: theme.palette.text.primary,
        };
    }
  };

  return {
    fontWeight: 'bold',
    ...getStatusColor(status),
  };
};
