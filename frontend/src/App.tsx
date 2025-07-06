import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

// Import pages (to be created)
import DashboardPage from './pages/DashboardPage';
import LoginPage from './pages/LoginPage';
import UsersPage from './pages/UsersPage';
import NodesPage from './pages/NodesPage';
import SettingsPage from './pages/SettingsPage';
import NotFoundPage from './pages/NotFoundPage';

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

// Create a theme instance
const theme = createTheme({
  palette: {
    mode: 'dark', // Enable dark mode by default
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
  },
});

// Main App component
const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </Router>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

// Component to define all routes
const AppRoutes: React.FC = () => {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={!isAuthenticated ? <LoginPage /> : <Navigate to="/" replace />} />
      
      {/* Protected routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      
      <Route
        path="/users/*"
        element={
          <ProtectedRoute requiredRole="admin">
            <UsersPage />
          </ProtectedRoute>
        }
      />
      
      <Route
        path="/nodes/*"
        element={
          <ProtectedRoute requiredRole="admin">
            <NodesPage />
          </ProtectedRoute>
        }
      />
      
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <SettingsPage />
          </ProtectedRoute>
        }
      />
      
      {/* 404 - Not Found */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
};

export default App;
