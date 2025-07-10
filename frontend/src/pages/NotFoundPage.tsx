import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import { Link } from 'react-router-dom';

const NotFoundPage: React.FC = () => {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        textAlign: 'center',
        p: 3,
      }}
    >
      <Typography variant="h1" component="h1" sx={{ fontWeight: 'bold', mb: 2 }}>
        404
      </Typography>
      <Typography variant="h5" component="h2" sx={{ mb: 4 }}>
        Страница не найдена
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        К сожалению, мы не смогли найти страницу, которую вы ищете.
      </Typography>
      <Button component={Link} to="/" variant="contained">
        Вернуться на главную
      </Button>
    </Box>
  );
};

export default NotFoundPage;
