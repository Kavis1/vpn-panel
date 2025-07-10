import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Container,
  Box,
  Avatar,
  Typography,
  TextField,
  Button,
  Grid,
  Paper,
  Alert,
  AlertTitle,
  InputAdornment,
  IconButton,
} from '@mui/material';
import { LockOutlined, Visibility, VisibilityOff } from '@mui/icons-material';
import { styled } from '@mui/material/styles';

const LoginPaper = styled(Paper)(({ theme }) => ({
  marginTop: theme.spacing(8),
  padding: theme.spacing(4),
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  borderRadius: (theme.shape.borderRadius as number) * 2,
}));

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [localError, setLocalError] = useState('');
  
  const navigate = useNavigate();
  const location = useLocation();
  const auth = useAuth();
  
  const from = (location.state as any)?.from?.pathname || '/';
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError('');

    if (!email || !password) {
      setLocalError('Пожалуйста, заполните все поля');
      return;
    }

    if (!email.includes('@')) {
      setLocalError('Введите корректный email адрес');
      return;
    }

    try {
      await auth.login(email, password);
      // Навигация происходит в AuthContext
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : 'Ошибка входа');
    }
  };
  
  const toggleShowPassword = () => {
    setShowPassword(!showPassword);
  };

  return (
    <Container component="main" maxWidth="xs">
      <LoginPaper elevation={3}>
        <Avatar sx={{ m: 1, bgcolor: 'secondary.main' }}>
          <LockOutlined />
        </Avatar>
        <Typography component="h1" variant="h5">
          VPN Admin Panel
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Панель администратора
        </Typography>
        
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3, width: '100%' }}>
          {(localError || auth.error) && (
            <Alert severity="error" sx={{ mb: 2 }}>
              <AlertTitle>Ошибка входа</AlertTitle>
              {localError || auth.error}
            </Alert>
          )}
          
          <TextField
            margin="normal"
            required
            fullWidth
            id="email"
            label="Email адрес"
            name="email"
            type="email"
            autoComplete="email"
            autoFocus
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={auth.isLoading}
          />
          
          <TextField
            margin="normal"
            required
            fullWidth
            name="password"
            label="Пароль"
            type={showPassword ? 'text' : 'password'}
            id="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={isLoading}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    aria-label="toggle password visibility"
                    onClick={toggleShowPassword}
                    edge="end"
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
          
          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{ mt: 3, mb: 2, py: 1.5 }}
            disabled={isLoading}
          >
            {isLoading ? 'Вход...' : 'Войти'}
          </Button>
          
          <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Box>
              <Link to="/forgot-password" style={{ textDecoration: 'none', color: 'inherit' }}>
                <Typography variant="body2" color="textSecondary">
                  Забыли пароль?
                </Typography>
              </Link>
            </Box>
          </Box>
        </Box>
      </LoginPaper>
      
      <Box mt={5} textAlign="center">
        <Typography variant="body2" color="textSecondary">
          © {new Date().getFullYear()} VPN Panel. Все права защищены.
        </Typography>
      </Box>
    </Container>
  );
};

export default LoginPage;
