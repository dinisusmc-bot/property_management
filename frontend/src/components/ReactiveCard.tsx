import React from 'react';
import { Box, Card, CardContent, Typography, SxProps } from '@mui/material';
import { glass } from '../theme';

interface ReactiveCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  color?: 'primary' | 'success' | 'warning' | 'error';
  icon?: React.ReactNode;
  sx?: SxProps;
}

export const ReactiveCard: React.FC<ReactiveCardProps> = ({
  title,
  value,
  subtitle,
  color = 'primary',
  icon,
  sx,
}) => {
  const colorMap = {
    primary: '#6366f1',
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
  };

  return (
    <Card sx={{ ...glass, ...sx }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          {icon && (
            <Box
              sx={{
                mr: 2,
                p: 1,
                borderRadius: 1,
                bgcolor: `${colorMap[color]}.100`,
                color: `${colorMap[color]}`,
              }}
            >
              {icon}
            </Box>
          )}
          <Typography variant="h6" color="text.secondary" fontWeight={600}>
            {title}
          </Typography>
        </Box>
        <Typography variant="h3" fontWeight={700} color="primary.contrastText">
          {value}
        </Typography>
        {subtitle && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};
