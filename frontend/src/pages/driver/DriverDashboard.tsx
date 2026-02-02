import { useState, useEffect, useCallback } from 'react'
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  Divider,
  List,
  ListItem,
  ListItemText,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material'
import {
  LocationOn as LocationIcon,
  Note as NoteIcon,
  Route as RouteIcon,
  Save as SaveIcon,
} from '@mui/icons-material'
import api from '../../services/api'

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
  trip_date: string
  passengers: number
  status: string
  notes: string | null
  vendor_notes: string | null
  last_checkin_location: string | null
  last_checkin_time: string | null
  stops: Stop[]
  vehicle: {
    id: number
    name: string
    capacity: number
  }
}

export default function DriverDashboard() {
  const [charter, setCharter] = useState<Charter | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notes, setNotes] = useState('')
  const [saving, setSaving] = useState(false)
  const [locationTracking, setLocationTracking] = useState(false)
  const [currentLocation, setCurrentLocation] = useState<string | null>(null)

  // Fetch driver's assigned charter
  const fetchCharter = async () => {
    try {
      setLoading(true)
      // Get current user's assigned charter
      const response = await api.get('/api/v1/charters/charters/driver/my-charter')
      if (response.data) {
        setCharter(response.data)
        setNotes(response.data.vendor_notes || '')
      } else {
        setError('No charter assigned to you')
      }
    } catch (err: any) {
      console.error('Failed to load charter:', err)
      setError(err.response?.data?.detail || 'Failed to load charter information')
    } finally {
      setLoading(false)
    }
  }

  // Save driver notes
  const handleSaveNotes = async () => {
    if (!charter) return
    
    try {
      setSaving(true)
      await api.patch(`/api/v1/charters/charters/${charter.id}/driver-notes`, {
        vendor_notes: notes
      })
      alert('Notes saved successfully')
      fetchCharter() // Refresh data
    } catch (err: any) {
      console.error('Failed to save notes:', err)
      alert('Failed to save notes: ' + (err.response?.data?.detail || err.message))
    } finally {
      setSaving(false)
    }
  }

  // Track location
  const updateLocation = useCallback(async (position: GeolocationPosition) => {
    if (!charter) return
    
    const { latitude, longitude } = position.coords
    const locationStr = `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`
    setCurrentLocation(locationStr)
    
    try {
      await api.patch(`/api/v1/charters/charters/${charter.id}/location`, {
        location: locationStr,
        timestamp: new Date().toISOString()
      })
    } catch (err) {
      console.error('Failed to update location:', err)
    }
  }, [charter])

  // Start/stop location tracking
  const toggleLocationTracking = () => {
    if (!locationTracking) {
      if ('geolocation' in navigator) {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            updateLocation(position)
            setLocationTracking(true)
            // Update location every 2 minutes
            const intervalId = setInterval(() => {
              navigator.geolocation.getCurrentPosition(updateLocation)
            }, 120000)
            // Store interval ID to clear later
            ;(window as any).locationInterval = intervalId
          },
          (error) => {
            alert('Failed to get location: ' + error.message)
          }
        )
      } else {
        alert('Geolocation is not supported by your browser')
      }
    } else {
      setLocationTracking(false)
      if ((window as any).locationInterval) {
        clearInterval((window as any).locationInterval)
      }
    }
  }

  useEffect(() => {
    fetchCharter()
    
    // Cleanup location tracking on unmount
    return () => {
      if ((window as any).locationInterval) {
        clearInterval((window as any).locationInterval)
      }
    }
  }, [])

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    )
  }

  if (!charter) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="info">No charter assigned to you at this time.</Alert>
      </Box>
    )
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        My Charter Assignment
      </Typography>

      <Grid container spacing={3}>
        {/* Charter Details */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Charter Details
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="caption" color="textSecondary">Trip Date</Typography>
                  <Typography variant="body1">{new Date(charter.trip_date).toLocaleDateString()}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="textSecondary">Status</Typography>
                  <Typography variant="body1">
                    <Chip label={charter.status} color={charter.status === 'in_progress' ? 'success' : 'default'} size="small" />
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="textSecondary">Passengers</Typography>
                  <Typography variant="body1">{charter.passengers}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="textSecondary">Vehicle</Typography>
                  <Typography variant="body1">{charter.vehicle.name}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="caption" color="textSecondary">Charter Notes</Typography>
                  <Typography variant="body2">{charter.notes || 'No notes'}</Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Location Tracking */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <LocationIcon />
                <Typography variant="h6">Location Tracking</Typography>
              </Box>
              <Divider sx={{ mb: 2 }} />
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="caption" color="textSecondary">Current Location</Typography>
                <Typography variant="body2">
                  {currentLocation || charter.last_checkin_location || 'Not tracked yet'}
                </Typography>
                {charter.last_checkin_time && (
                  <Typography variant="caption" color="textSecondary" display="block">
                    Last updated: {new Date(charter.last_checkin_time).toLocaleString()}
                  </Typography>
                )}
              </Box>
              
              <Button
                variant={locationTracking ? 'outlined' : 'contained'}
                color={locationTracking ? 'error' : 'primary'}
                startIcon={<LocationIcon />}
                onClick={toggleLocationTracking}
                fullWidth
              >
                {locationTracking ? 'Stop Tracking' : 'Start Location Tracking'}
              </Button>
              
              {locationTracking && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  Location is being tracked every 2 minutes
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Itinerary */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" alignItems="center" gap={1} mb={2}>
              <RouteIcon />
              <Typography variant="h6">Trip Itinerary</Typography>
            </Box>
            <Divider sx={{ mb: 2 }} />
            
            {charter.stops && charter.stops.length > 0 ? (
              <List>
                {charter.stops.sort((a, b) => a.sequence - b.sequence).map((stop) => (
                  <ListItem key={stop.id} sx={{ borderLeft: 3, borderColor: 'primary.main', mb: 1 }}>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Chip label={`Stop ${stop.sequence}`} size="small" />
                          <Typography>{stop.location}</Typography>
                        </Box>
                      }
                      secondary={
                        <Box sx={{ mt: 1 }}>
                          {stop.arrival_time && (
                            <Typography variant="body2">
                              Arrival: {new Date(stop.arrival_time).toLocaleString()}
                            </Typography>
                          )}
                          {stop.departure_time && (
                            <Typography variant="body2">
                              Departure: {new Date(stop.departure_time).toLocaleString()}
                            </Typography>
                          )}
                          {stop.notes && (
                            <Typography variant="body2" color="textSecondary" sx={{ mt: 0.5 }}>
                              {stop.notes}
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Alert severity="info">No itinerary stops defined</Alert>
            )}
          </Paper>
        </Grid>

        {/* Driver Notes */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" alignItems="center" gap={1} mb={2}>
              <NoteIcon />
              <Typography variant="h6">My Notes</Typography>
            </Box>
            <Divider sx={{ mb: 2 }} />
            
            <TextField
              fullWidth
              multiline
              rows={6}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add notes about the trip, passenger behavior, road conditions, etc..."
              variant="outlined"
            />
            
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                startIcon={<SaveIcon />}
                onClick={handleSaveNotes}
                disabled={saving}
              >
                {saving ? 'Saving...' : 'Save Notes'}
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
