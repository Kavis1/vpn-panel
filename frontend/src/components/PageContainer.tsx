import React, { ReactNode } from 'react';
import { Box, BoxProps } from '@mui/material';

interface PageContainerProps extends BoxProps {
  children: ReactNode;
}

export const PageContainer: React.FC<PageContainerProps> = ({ children, ...props }) => {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        p: { xs: 2, sm: 3, md: 4 },
        maxWidth: '100%',
        mx: 'auto',
        width: '100%',
      }}
      {...props}
    >
      {children}
    </Box>
  );
};

export default PageContainer;
