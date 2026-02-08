import { useEffect, useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Divider,
  Chip,
} from '@mui/material'
import { useCalculateQuote } from '../hooks/usePricing'
import { PricingRequest, PricingResponse, PricingLineItem } from '../types/pricing.types'

interface PricingCalculatorProps {
  request: PricingRequest
  onPricingCalculated?: (pricing: PricingResponse) => void
}

export function PricingCalculator({ request, onPricingCalculated }: PricingCalculatorProps) {
  const calculateMutation = useCalculateQuote()
  const [pricing, setPricing] = useState<PricingResponse | null>(null)

  // Calculate pricing when request changes
  useEffect(() => {
    if (request.trip_date && request.vehicle_id && request.passengers) {
      calculateMutation.mutate(request, {
        onSuccess: (data) => {
          setPricing(data)
          onPricingCalculated?.(data)
        },
      })
    }
  }, [
    request.client_id,
    request.vehicle_id,
    request.passengers,
    request.trip_date,
    request.total_miles,
    request.trip_hours,
    request.is_overnight,
    request.is_weekend,
    request.is_holiday,
    request.additional_fees,
    request.notes,
  ])

  if (calculateMutation.isPending) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" alignItems="center" gap={2}>
            <CircularProgress size={24} />
            <Typography>Calculating pricing...</Typography>
          </Box>
        </CardContent>
      </Card>
    )
  }

  if (calculateMutation.isError) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error">
            Failed to calculate pricing. Please check your inputs and try again.
          </Alert>
        </CardContent>
      </Card>
    )
  }

  if (!pricing) {
    return (
      <Card>
        <CardContent>
          <Typography color="text.secondary">
            Fill in trip details to calculate pricing
          </Typography>
        </CardContent>
      </Card>
    )
  }

  const { breakdown } = pricing
  const lineItems: PricingLineItem[] = [
    { description: 'Base Cost', amount: breakdown.base_cost },
    { description: 'Mileage Cost', amount: breakdown.mileage_cost },
    { description: 'Time Based Cost', amount: breakdown.time_based_cost },
    { description: 'Additional Fees', amount: breakdown.additional_fees },
    { description: 'Fuel Surcharge', amount: breakdown.fuel_surcharge },
  ].filter((item) => item.amount > 0)

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Price Breakdown
        </Typography>

        {/* Line Items */}
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Description</TableCell>
                <TableCell align="right">Amount</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {lineItems.map((item, index) => (
                <TableRow key={index}>
                  <TableCell>
                    {item.description}
                  </TableCell>
                  <TableCell align="right">
                    ${item.amount.toFixed(2)}
                  </TableCell>
                </TableRow>
              ))}

              {/* Subtotal */}
              <TableRow>
                <TableCell colSpan={2}>
                  <Divider sx={{ my: 1 }} />
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>
                  <Typography variant="subtitle2">Subtotal</Typography>
                </TableCell>
                <TableCell align="right">
                  <Typography variant="subtitle2">
                    ${breakdown.subtotal.toFixed(2)}
                  </Typography>
                </TableCell>
              </TableRow>

              {/* Total */}
              <TableRow>
                <TableCell colSpan={2}>
                  <Divider sx={{ my: 1 }} />
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>
                  <Typography variant="h6">Total</Typography>
                </TableCell>
                <TableCell align="right">
                  <Typography variant="h6">
                    ${breakdown.total_cost.toFixed(2)}
                  </Typography>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>

        {/* Trip Summary */}
        <Box mt={2}>
          <Typography variant="caption" color="text.secondary">
            {request.trip_hours ? `${request.trip_hours} hours` : 'Hours not set'}
            {request.total_miles !== undefined && ` • ${request.total_miles} miles`}
          </Typography>
        </Box>

        {/* Compliance Status */}
        <Box mt={1} display="flex" gap={1} flexWrap="wrap">
          {pricing.dot_compliant ? (
            <Chip
              label="DOT Compliant"
              color="success"
              size="small"
            />
          ) : (
            <Chip
              label="DOT Warning"
              color="warning"
              size="small"
            />
          )}
          {request.is_overnight && (
            <Chip label="Overnight" size="small" />
          )}
          {request.is_weekend && (
            <Chip label="Weekend" size="small" />
          )}
          {request.is_holiday && (
            <Chip label="Holiday" size="small" />
          )}
        </Box>
      </CardContent>
    </Card>
  )
}
