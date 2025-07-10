/**
 * Utility components for Material-UI Grid v5 migration
 */
import React from 'react';
import { Grid, GridProps } from '@mui/material';

/**
 * Wrapper for Grid item with proper v5 API
 */
interface GridItemProps extends Omit<GridProps, 'item'> {
  xs?: number | 'auto';
  sm?: number | 'auto';
  md?: number | 'auto';
  lg?: number | 'auto';
  xl?: number | 'auto';
  children: React.ReactNode;
}

export const GridItem: React.FC<GridItemProps> = ({ 
  xs, 
  sm, 
  md, 
  lg, 
  xl, 
  children, 
  ...props 
}) => {
  return (
    <Grid 
      size={{ xs, sm, md, lg, xl }}
      {...props}
    >
      {children}
    </Grid>
  );
};

/**
 * Wrapper for Grid container with proper v5 API
 */
interface GridContainerProps extends Omit<GridProps, 'container'> {
  spacing?: number;
  children: React.ReactNode;
}

export const GridContainer: React.FC<GridContainerProps> = ({ 
  spacing, 
  children, 
  ...props 
}) => {
  return (
    <Grid 
      container 
      spacing={spacing}
      {...props}
    >
      {children}
    </Grid>
  );
};
