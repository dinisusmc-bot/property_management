import {
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Alert,
  LinearProgress,
} from '@mui/material'
import { useConversionFunnel } from '../hooks/useDashboard'
import { ArrowForward } from '@mui/icons-material'

export function ConversionFunnelCard() {
  const { data: funnel, isLoading, isError } = useConversionFunnel('month')

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

  if (isError || !funnel) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error">Failed to load conversion funnel</Alert>
        </CardContent>
      </Card>
    )
  }

  const maxValue = Math.max(...funnel.funnel.map((stage) => stage.count), 1)

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Conversion Funnel ({funnel.period})
        </Typography>

        <Box mt={3}>
          {funnel.funnel.map((stage, index) => (
            <Box key={stage.stage} mb={3}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                <Typography variant="body2" fontWeight="medium">
                  {stage.stage}
                </Typography>
                <Typography variant="h6">{stage.count}</Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={(stage.count / maxValue) * 100}
                sx={{ height: 8, borderRadius: 1 }}
              />
              {index < funnel.funnel.length - 1 && (
                <Box display="flex" alignItems="center" justifyContent="center" mt={1}>
                  <ArrowForward sx={{ color: 'text.secondary' }} />
                  <Typography variant="caption" color="text.secondary" ml={1}>
                    {stage.percentage.toFixed(1)}% of total
                  </Typography>
                </Box>
              )}
            </Box>
          ))}

          {/* Overall Conversion */}
          <Box
            mt={3}
            p={2}
            sx={{ backgroundColor: 'primary.50', borderRadius: 1 }}
            textAlign="center"
          >
            <Typography variant="caption" color="text.secondary" display="block">
              Overall Conversion Rate
            </Typography>
            <Typography variant="h4" color="primary">
              {funnel.conversion_rate.toFixed(1)}%
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  )
}
