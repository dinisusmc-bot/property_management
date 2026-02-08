import { useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Alert,
  CircularProgress,
  Link,
} from '@mui/material'
import { CheckCircle, Warning } from '@mui/icons-material'
import { useCheckDOTCompliance } from '../hooks/usePricing'
import { DOTCompliance } from '../types/pricing.types'

interface DOTComplianceCheckProps {
  distanceMiles?: number
  stopsCount?: number
  tripHours?: number
  isMultiDay?: boolean
  onComplianceChecked?: (compliance: DOTCompliance) => void
}

export function DOTComplianceCheck({
  distanceMiles,
  stopsCount = 0,
  tripHours,
  isMultiDay = false,
  onComplianceChecked,
}: DOTComplianceCheckProps) {
  const checkMutation = useCheckDOTCompliance()

  useEffect(() => {
    if (distanceMiles !== undefined && distanceMiles > 0) {
      checkMutation.mutate(
        {
          distance_miles: distanceMiles,
          stops_count: stopsCount,
          trip_hours: tripHours,
          is_multi_day: isMultiDay,
        },
        {
          onSuccess: (data) => {
            onComplianceChecked?.(data)
          },
        }
      )
    }
  }, [distanceMiles, stopsCount, tripHours, isMultiDay])

  if (!distanceMiles || distanceMiles === 0) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            DOT Compliance
          </Typography>
          <Typography color="text.secondary" variant="body2">
            Enter trip details to check DOT compliance
          </Typography>
        </CardContent>
      </Card>
    )
  }

  if (checkMutation.isPending) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            DOT Compliance
          </Typography>
          <Box display="flex" alignItems="center" gap={2}>
            <CircularProgress size={24} />
            <Typography>Checking DOT compliance...</Typography>
          </Box>
        </CardContent>
      </Card>
    )
  }

  if (checkMutation.isError) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            DOT Compliance
          </Typography>
          <Alert severity="error">
            Failed to check DOT compliance
          </Alert>
        </CardContent>
      </Card>
    )
  }

  const compliance = checkMutation.data

  if (!compliance) {
    return null
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          DOT Compliance Check
        </Typography>

        {/* Compliance Status */}
        <Alert
          severity={compliance.compliant ? 'success' : 'warning'}
          icon={compliance.compliant ? <CheckCircle /> : <Warning />}
          sx={{ mb: 2 }}
        >
          <Typography variant="subtitle2" gutterBottom>
            {compliance.compliant
              ? 'Trip is DOT Compliant'
              : 'DOT Compliance Warning'}
          </Typography>
          {(compliance.violations.length > 0 || compliance.warnings.length > 0) && (
            <Box>
              {compliance.violations.map((violation, idx) => (
                <Typography key={`violation-${idx}`} variant="body2">
                  • {violation}
                </Typography>
              ))}
              {compliance.warnings.map((warning, idx) => (
                <Typography key={idx} variant="body2">
                  • {warning}
                </Typography>
              ))}
            </Box>
          )}
        </Alert>

        {/* Trip Details */}
        <Box mb={2}>
          <Typography variant="caption" color="text.secondary" display="block">
            Estimated Driving Hours: {compliance.estimated_hours.driving_hours}
          </Typography>
          <Typography variant="caption" color="text.secondary" display="block">
            Estimated Duty Hours: {compliance.estimated_hours.total_duty_hours}
          </Typography>
          <Typography variant="caption" color="text.secondary" display="block">
            Max Daily Driving: {compliance.max_daily_driving} hours
          </Typography>
          <Typography variant="caption" color="text.secondary" display="block">
            Max Daily Duty: {compliance.max_daily_duty} hours
          </Typography>
          {compliance.minimum_rest_required_hours !== undefined && (
            <Typography variant="caption" color="text.secondary" display="block">
              Minimum Rest Required: {compliance.minimum_rest_required_hours} hours
            </Typography>
          )}
          {compliance.earliest_next_trip && (
            <Typography variant="caption" color="text.secondary" display="block">
              Earliest Next Trip: {compliance.earliest_next_trip}
            </Typography>
          )}
        </Box>

        {/* DOT Reference Link */}
        <Box>
          <Typography variant="caption" color="text.secondary">
            Federal DOT regulations require drivers to follow Hours of Service (HOS) rules.{' '}
            <Link
              href="https://www.fmcsa.dot.gov/regulations/hours-service"
              target="_blank"
              rel="noopener noreferrer"
            >
              Learn more
            </Link>
          </Typography>
        </Box>
      </CardContent>
    </Card>
  )
}
