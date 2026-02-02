import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Chip,
  Button,
  TextField,
  Divider,
  Alert,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  IconButton
} from '@mui/material'
import api from '../services/api'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import LocationOnIcon from '@mui/icons-material/LocationOn'
import SaveIcon from '@mui/icons-material/Save'
import MyLocationIcon from '@mui/icons-material/MyLocation'
import StopCircleIcon from '@mui/icons-material/StopCircle'

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

export default function VendorCharterDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [charter, setCharter] = useState<Charter | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [vendorNotes, setVendorNotes] = useState('')
  const [saving, setSaving] = useState(false)
  const [locationTracking, setLocationTracking] = useState(() => {
    // Initialize from localStorage
    const savedTracking = localStorage.getItem(`tracking_charter_${id}`)
    return savedTracking === 'true'
  })
  const [currentLocation, setCurrentLocation] = useState<string>('')
  const [lastCheckinDisplay, setLastCheckinDisplay] = useState<{location: string, time: string} | null>(null)
  const trackingIntervalRef = useRef<number | null>(null)
  const charterRef = useRef<Charter | null>(null)

  // Keep charterRef in sync with charter state
  useEffect(() => {
    charterRef.current = charter
  }, [charter])

  // Persist tracking state to localStorage
  useEffect(() => {
    if (id) {
      localStorage.setItem(`tracking_charter_${id}`, locationTracking.toString())
    }
  }, [locationTracking, id])

  useEffect(() => {
    if (id) {
      fetchCharter()
    }
  }, [id])

  useEffect(() => {
    if (locationTracking) {
      // Start tracking when enabled
      if (!navigator.geolocation) {
        setError('Geolocation is not supported by your browser')
        setLocationTracking(false)
        return
      }

      // Clear any existing interval
      if (trackingIntervalRef.current !== null) {
        clearInterval(trackingIntervalRef.current)
        trackingIntervalRef.current = null
      }

      // Update immediately
      updateLocation()
      
      // Then update every 60 seconds (1 minute)
      const interval = window.setInterval(() => {
        updateLocation()
      }, 60000)
      trackingIntervalRef.current = interval
    } else {
      // Stop tracking when disabled
      if (trackingIntervalRef.current !== null) {
        clearInterval(trackingIntervalRef.current)
        trackingIntervalRef.current = null
      }
    }

    // Cleanup on unmount or when tracking changes
    return () => {
      if (trackingIntervalRef.current !== null) {
        clearInterval(trackingIntervalRef.current)
        trackingIntervalRef.current = null
      }
    }
  }, [locationTracking])

  const fetchCharter = async () => {
    try {
      setLoading(true)
      setError('')
      const response = await api.get(`/api/v1/charters/charters/${id}`)
      setCharter(response.data)
      setVendorNotes(response.data.vendor_notes || '')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load charter')
    } finally {
      setLoading(false)
    }
  }

  const updateLocation = useCallback(() => {
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords
        const locationString = `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`
        
        setCurrentLocation((prev: string) => prev !== locationString ? locationString : prev)
        
        const currentCharter = charterRef.current
        if (currentCharter) {
          try {
            const checkinTime = new Date().toISOString()
            await api.post(`/api/v1/charters/charters/${currentCharter.id}/checkin`, {
              location: locationString,
              checkin_time: checkinTime
            })
            setLastCheckinDisplay({ location: locationString, time: checkinTime })
          } catch (err) {
            console.error('Failed to update location', err)
          }
        }
      },
      (error) => {
        console.error('Location error:', error)
        setError('Failed to get location: ' + error.message)
      },
      {
        enableHighAccuracy: true,
        timeout: 5000,
        maximumAge: 0
      }
    )
  }, [])

  const handleSaveNotes = async () => {
    if (!charter) return

    try {
      setSaving(true)
      await api.put(`/api/v1/charters/charters/${charter.id}`, {
        vendor_notes: vendorNotes
      })
      setError('')
      await fetchCharter()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save notes')
    } finally {
      setSaving(false)
    }
  }

  const handleManualCheckIn = async () => {
    if (!charter) return

    const location = prompt('Enter your current location:')
    if (!location) return

    try {
      await api.post(`/api/v1/charters/charters/${charter.id}/checkin`, {
        location,
        checkin_time: new Date().toISOString()
      })
      await fetchCharter()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to check in')
    }
  }

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    )
  }

  if (!charter) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">{error || 'Charter not found'}</Alert>
        <Button 
          startIcon={<ArrowBackIcon />} 
          onClick={() => navigate('/vendor')}
          sx={{ mt: 2 }}
        >
          Back to My Charters
        </Button>
      </Container>
    )
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <IconButton onClick={() => navigate('/vendor')}>
          <ArrowBackIcon />
        </IconButton>
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h4">
            Charter #{charter.id}
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            {new Date(charter.trip_date).toLocaleDateString('en-US', { 
              weekday: 'long', 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })}
          </Typography>
        </Box>
        <Chip label={charter.status} color="primary" />
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Charter Info */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Trip Information
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Vehicle</Typography>
              <Typography variant="body1">
                {charter.vehicle.name} ({charter.vehicle.capacity} passengers)
              </Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Passengers</Typography>
              <Typography variant="body1">{charter.passengers}</Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Trip Duration</Typography>
              <Typography variant="body1">{charter.trip_hours} hours</Typography>
            </Box>

            {charter.notes && (
              <Box sx={{ mt: 3, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                <Typography variant="caption" color="info.dark" sx={{ fontWeight: 'bold', display: 'block', mb: 1 }}>
                  Special Instructions
                </Typography>
                <Typography variant="body2">
                  {charter.notes}
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Location Tracking */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Location Tracking
            </Typography>
            <Divider sx={{ mb: 2 }} />

            <Box sx={{ mb: 2 }}>
              <Button
                variant={locationTracking ? "outlined" : "contained"}
                color={locationTracking ? "error" : "primary"}
                startIcon={locationTracking ? <StopCircleIcon /> : <MyLocationIcon />}
                onClick={() => setLocationTracking(!locationTracking)}
                fullWidth
                sx={{ mb: 2 }}
              >
                {locationTracking ? 'Stop Auto Tracking' : 'Start Auto Tracking'}
              </Button>

              <Button
                variant="outlined"
                startIcon={<LocationOnIcon />}
                onClick={handleManualCheckIn}
                fullWidth
                disabled={locationTracking}
              >
                Manual Check-In
              </Button>
            </Box>

            {locationTracking && currentLocation && (
              <Alert severity="success" sx={{ mb: 2 }}>
                Tracking active: {currentLocation}
              </Alert>
            )}

            {(lastCheckinDisplay || charter.last_checkin_location) && (
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="caption" color="textSecondary">
                    Last Check-in
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 'bold', mt: 0.5 }}>
                    {lastCheckinDisplay?.location || charter.last_checkin_location}
                  </Typography>
                  {(lastCheckinDisplay?.time || charter.last_checkin_time) && (
                    <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mt: 0.5 }}>
                      {new Date(lastCheckinDisplay?.time || charter.last_checkin_time!).toLocaleString()}
                    </Typography>
                  )}
                </CardContent>
              </Card>
            )}
          </Paper>
        </Grid>

        {/* Trip Itinerary */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Trip Itinerary
            </Typography>
            <Divider sx={{ mb: 2 }} />

            {charter.stops.length === 0 ? (
              <Typography variant="body2" color="textSecondary">
                No stops defined for this charter
              </Typography>
            ) : (
              <List>
                {charter.stops
                  .sort((a, b) => a.sequence - b.sequence)
                  .map((stop, index) => (
                    <ListItem key={stop.id} divider={index < charter.stops.length - 1}>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Chip label={`Stop ${stop.sequence + 1}`} size="small" />
                            <Typography variant="body1">
                              {stop.location}
                            </Typography>
                          </Box>
                        }
                        secondary={
                          <Box>
                            {stop.arrival_time && (
                              <Typography variant="caption" display="block" color="primary">
                                Arrival: {new Date(stop.arrival_time).toLocaleTimeString('en-US', {
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })}
                              </Typography>
                            )}
                            {stop.departure_time && (
                              <Typography variant="caption" display="block" color="textSecondary">
                                Departure: {new Date(stop.departure_time).toLocaleTimeString('en-US', {
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })}
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
            )}
          </Paper>
        </Grid>

        {/* Vendor Notes */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              My Notes
            </Typography>
            <Divider sx={{ mb: 2 }} />

            <TextField
              fullWidth
              multiline
              rows={8}
              value={vendorNotes}
              onChange={(e) => setVendorNotes(e.target.value)}
              placeholder="Add notes about the trip, traffic conditions, passenger requests, etc."
              sx={{ mb: 2 }}
            />

            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSaveNotes}
              disabled={saving}
              fullWidth
            >
              {saving ? 'Saving...' : 'Save Notes'}
            </Button>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  )
}
