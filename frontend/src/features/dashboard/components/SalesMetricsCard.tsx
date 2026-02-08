import { Card, CardContent, Typography, Box, CircularProgress, Alert } from '@mui/material'
import { useSalesMetrics } from '../hooks/useDashboard'
import { StatsCard } from './StatsCard'
import {
  ContactPhone,
  CheckCircle,
  Groups,
  Timeline,
} from '@mui/icons-material'

export function SalesMetricsCard() {
  const { data: metrics, isLoading, isError } = useSalesMetrics('month')

  if (isLoading) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    )
  }

  if (isError || !metrics) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error">Failed to load sales metrics</Alert>
        </CardContent>
      </Card>
    )
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Sales Performance
      </Typography>

      <Box display="grid" gridTemplateColumns="repeat(auto-fit, minmax(250px, 1fr))" gap={2}>
        <StatsCard
          title="Total Leads"
          value={metrics.total_leads}
          icon={<ContactPhone />}
        />

        <StatsCard
          title="New Leads"
          value={metrics.new_leads}
          icon={<Timeline />}
        />

        <StatsCard
          title="Converted Leads"
          value={metrics.converted}
          icon={<CheckCircle />}
        />

        <StatsCard
          title="Conversion Rate"
          value={`${metrics.conversion_rate.toFixed(1)}%`}
          icon={<Groups />}
        />
      </Box>

      {/* Period Breakdown */}
      <Box mt={3}>
        <Card variant="outlined">
          <CardContent>
            <Typography variant="subtitle2" gutterBottom>
              Performance Breakdown
            </Typography>
            <Box display="grid" gridTemplateColumns="repeat(4, 1fr)" gap={2} mt={2}>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Contacted
                </Typography>
                <Typography variant="body2">
                  {metrics.contacted}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Qualified
                </Typography>
                <Typography variant="body2">
                  {metrics.qualified}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Avg Response Time
                </Typography>
                <Typography variant="body2">
                  {metrics.avg_response_time_hours.toFixed(1)}h
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Active Agents
                </Typography>
                <Typography variant="body2">
                  {metrics.active_agents}
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Box>
    </Box>
  )
}
