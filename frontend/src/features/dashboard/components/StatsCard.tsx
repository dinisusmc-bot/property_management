import { Card, CardContent, Typography, Box, Skeleton } from '@mui/material'
import { TrendingUp, TrendingDown } from '@mui/icons-material'

interface StatsCardProps {
  title: string
  value: string | number
  trend?: number
  trendLabel?: string
  icon?: React.ReactNode
  loading?: boolean
}

export function StatsCard({ title, value, trend, trendLabel, icon, loading }: StatsCardProps) {
  if (loading) {
    return (
      <Card>
        <CardContent>
          <Skeleton variant="text" width="60%" />
          <Skeleton variant="text" width="40%" height={40} />
          <Skeleton variant="text" width="50%" />
        </CardContent>
      </Card>
    )
  }

  const isPositive = trend !== undefined && trend >= 0

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
          <Typography variant="body2" color="text.secondary">
            {title}
          </Typography>
          {icon && <Box color="primary.main">{icon}</Box>}
        </Box>

        <Typography variant="h4" component="div" mb={1}>
          {value}
        </Typography>

        {trend !== undefined && (
          <Box display="flex" alignItems="center" gap={0.5}>
            {isPositive ? (
              <TrendingUp fontSize="small" sx={{ color: 'success.main' }} />
            ) : (
              <TrendingDown fontSize="small" sx={{ color: 'error.main' }} />
            )}
            <Typography
              variant="caption"
              sx={{ color: isPositive ? 'success.main' : 'error.main' }}
            >
              {Math.abs(trend).toFixed(1)}%
            </Typography>
            {trendLabel && (
              <Typography variant="caption" color="text.secondary">
                {trendLabel}
              </Typography>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  )
}
