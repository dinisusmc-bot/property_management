import { Box, Typography, Grid } from '@mui/material'
import { SalesMetricsCard } from '../../features/dashboard/components/SalesMetricsCard'
import { ConversionFunnelCard } from '../../features/dashboard/components/ConversionFunnelCard'
import { TopPerformersCard } from '../../features/dashboard/components/TopPerformersCard'
import { RecentActivityCard } from '../../features/dashboard/components/RecentActivityCard'
import { QuickActionsCard } from '../../features/dashboard/components/QuickActionsCard'

export default function DashboardPage() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Sales Dashboard
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Welcome back! Here's your sales performance overview.
      </Typography>

      <Box mt={3}>
        {/* Sales Metrics */}
        <Box mb={3}>
          <SalesMetricsCard />
        </Box>

        {/* Main Content Grid */}
        <Grid container spacing={3}>
          {/* Left Column */}
          <Grid item xs={12} lg={8}>
            {/* Conversion Funnel */}
            <Box mb={3}>
              <ConversionFunnelCard />
            </Box>

            {/* Recent Activity */}
            <Box>
              <RecentActivityCard />
            </Box>
          </Grid>

          {/* Right Column */}
          <Grid item xs={12} lg={4}>
            {/* Quick Actions */}
            <Box mb={3}>
              <QuickActionsCard />
            </Box>

            {/* Top Performers */}
            <Box>
              <TopPerformersCard />
            </Box>
          </Grid>
        </Grid>
      </Box>
    </Box>
  )
}
