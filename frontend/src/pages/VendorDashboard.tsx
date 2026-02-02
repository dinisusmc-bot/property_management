import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Container,
  Paper,
  Typography,
  Box,
  Chip,
  Button,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material'
import { useAuthStore } from '../store/authStore'
import api from '../services/api'

interface Vehicle {
  id: number
  name: string
  capacity: number
}

interface Stop {
  id: number
  sequence: number
  location: string
  arrival_time: string | null
  departure_time: string | null
  notes: string | null
}

interface Charter {
  id: number
  client_id: number
  vehicle: Vehicle
  trip_date: string
  passengers: number
  trip_hours: number
  status: string
  notes: string | null
  vendor_notes: string | null
  last_checkin_location: string | null
  last_checkin_time: string | null
  stops: Stop[]
}

export default function VendorDashboard() {
  const user = useAuthStore(state => state.user)
  const navigate = useNavigate()
  const [charters, setCharters] = useState<Charter[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchMyCharters()
  }, [user?.id])

  const fetchMyCharters = async () => {
    try {
      setLoading(true)
      setError('')
      // Fetch all charters assigned to this vendor
      const response = await api.get(`/api/v1/charters/charters?vendor_id=${user?.id}`)
      setCharters(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load charters')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed': return 'success'
      case 'in_progress': return 'warning'
      case 'completed': return 'success'
      case 'cancelled': return 'error'
      default: return 'default'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', { 
      weekday: 'short', 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    })
  }

  const formatTime = (dateString: string | null) => {
    if (!dateString) return 'Never'
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    )
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          My Charters
        </Typography>
        <Typography variant="subtitle1" color="textSecondary">
          Welcome, {user?.full_name}
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {charters.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="textSecondary">
            No charters assigned
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
            You don't have any charters assigned to you at the moment.
          </Typography>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Charter ID</TableCell>
                <TableCell>Date</TableCell>
                <TableCell>Vehicle</TableCell>
                <TableCell>Passengers</TableCell>
                <TableCell>Stops</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Last Check-In</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {charters.map((charter) => (
                <TableRow 
                  key={charter.id}
                  sx={{ '&:hover': { backgroundColor: 'action.hover' } }}
                >
                  <TableCell>#{charter.id}</TableCell>
                  <TableCell>{formatDate(charter.trip_date)}</TableCell>
                  <TableCell>
                    {charter.vehicle.name}
                    <Typography variant="caption" display="block" color="textSecondary">
                      Capacity: {charter.vehicle.capacity}
                    </Typography>
                  </TableCell>
                  <TableCell>{charter.passengers}</TableCell>
                  <TableCell>{charter.stops.length} stops</TableCell>
                  <TableCell>
                    <Chip 
                      label={charter.status} 
                      color={getStatusColor(charter.status)} 
                      size="small" 
                    />
                  </TableCell>
                  <TableCell>
                    {charter.last_checkin_time ? (
                      <>
                        {formatTime(charter.last_checkin_time)}
                        {charter.last_checkin_location && (
                          <Typography variant="caption" display="block" color="textSecondary">
                            {charter.last_checkin_location}
                          </Typography>
                        )}
                      </>
                    ) : (
                      <Typography variant="caption" color="textSecondary">
                        No check-ins yet
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell align="center">
                    <Button
                      variant="contained"
                      size="small"
                      onClick={() => navigate(`/vendor/charter/${charter.id}`)}
                    >
                      View Details
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Container>
  )
}
