/**
 * Client Trip History Tab Component
 */
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Typography,
  TextField,
  MenuItem,
  Paper
} from '@mui/material'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '@/services/api'
import { format } from 'date-fns'

interface ClientTripsTabProps {
  clientId: number
}

export default function ClientTripsTab({ clientId }: ClientTripsTabProps) {
  const [statusFilter, setStatusFilter] = useState('all')
  
  const { data: trips, isLoading } = useQuery({
    queryKey: ['client-trips', clientId, statusFilter],
    queryFn: async () => {
      const params = statusFilter !== 'all' ? `?status=${statusFilter}` : ''
      const response = await api.get(`/api/v1/charters?client_id=${clientId}${params}`)
      return response.data
    }
  })
  
  const getStatusColor = (status: string) => {
    const colors: Record<string, any> = {
      quote: 'info',
      approved: 'warning',
      booked: 'primary',
      confirmed: 'success',
      in_progress: 'secondary',
      completed: 'success',
      cancelled: 'error'
    }
    return colors[status] || 'default'
  }

  if (isLoading) {
    return <Typography>Loading...</Typography>
  }

  return (
    <Box>
      {/* Filter */}
      <Box mb={2} display="flex" justifyContent="space-between" alignItems="center">
        <Typography variant="h6">
          Trip History ({trips?.length || 0} trips)
        </Typography>
        <TextField
          select
          size="small"
          label="Filter by Status"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          sx={{ minWidth: 200 }}
        >
          <MenuItem value="all">All Statuses</MenuItem>
          <MenuItem value="quote">Quotes</MenuItem>
          <MenuItem value="booked">Booked</MenuItem>
          <MenuItem value="completed">Completed</MenuItem>
          <MenuItem value="cancelled">Cancelled</MenuItem>
        </TextField>
      </Box>
      
      {/* Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Reference #</TableCell>
              <TableCell>Date</TableCell>
              <TableCell>Route</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Passengers</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Total Price</TableCell>
              <TableCell align="right">Balance Due</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {trips?.map((trip: any) => (
              <TableRow key={trip.id} hover>
                <TableCell>{trip.reference_number || '-'}</TableCell>
                <TableCell>
                  {trip.pickup_date ? format(new Date(trip.pickup_date), 'MMM dd, yyyy') : '-'}
                </TableCell>
                <TableCell>
                  <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                    {trip.pickup_location || '-'} → {trip.dropoff_location || '-'}
                  </Typography>
                </TableCell>
                <TableCell>{trip.trip_type || '-'}</TableCell>
                <TableCell>{trip.passengers || 0}</TableCell>
                <TableCell>
                  <Chip
                    label={trip.status || 'unknown'}
                    color={getStatusColor(trip.status || '')}
                    size="small"
                  />
                </TableCell>
                <TableCell align="right">
                  ${trip.total_price?.toFixed(2) || '0.00'}
                </TableCell>
                <TableCell align="right">
                  <Typography
                    variant="body2"
                    color={trip.balance_due > 0 ? 'error.main' : 'success.main'}
                  >
                    ${trip.balance_due?.toFixed(2) || '0.00'}
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  <Typography variant="body2">View</Typography>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      
      {trips?.length === 0 && !isLoading && (
        <Box textAlign="center" py={4}>
          <Typography color="text.secondary">
            No trips found for this client
          </Typography>
        </Box>
      )}
    </Box>
  )
}
