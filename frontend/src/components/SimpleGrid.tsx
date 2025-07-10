import React from 'react';

interface SimpleGridProps {
  container?: boolean;
  spacing?: number;
  children: React.ReactNode;
  xs?: number;
  sm?: number;
  md?: number;
  lg?: number;
  item?: boolean;
  sx?: any;
  [key: string]: any;
}

export const SimpleGrid: React.FC<SimpleGridProps> = ({ 
  container, 
  spacing = 2, 
  children, 
  xs, 
  sm, 
  md, 
  lg,
  item,
  sx,
  ...props 
}) => {
  if (container) {
    return (
      <div 
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: `${spacing * 8}px`,
          ...sx
        }}
        {...props}
      >
        {children}
      </div>
    );
  }

  // Calculate flex basis based on breakpoints
  let flexBasis = '100%';
  if (xs === 12) flexBasis = '100%';
  else if (xs === 6) flexBasis = '50%';
  else if (xs === 4) flexBasis = '33.333%';
  else if (xs === 3) flexBasis = '25%';
  
  if (md === 12) flexBasis = '100%';
  else if (md === 8) flexBasis = '66.666%';
  else if (md === 6) flexBasis = '50%';
  else if (md === 4) flexBasis = '33.333%';
  else if (md === 3) flexBasis = '25%';

  return (
    <div 
      style={{
        flex: `1 1 ${flexBasis}`,
        minWidth: md === 4 ? '300px' : md === 6 ? '400px' : md === 8 ? '600px' : '250px',
        padding: '8px',
        ...sx
      }}
      {...props}
    >
      {children}
    </div>
  );
};

export default SimpleGrid;
