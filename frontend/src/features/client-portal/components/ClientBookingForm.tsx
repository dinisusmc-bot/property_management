/**
 * Client Booking Form
 * Booking creation form for client portal
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Card,
  CardContent
} from '@mui/material'
import {
  Schedule as ScheduleIcon,
  LocationOn as LocationIcon,
  People as PeopleIcon,
  AttachMoney as MoneyIcon
} from '@mui/icons-material'
import { useCreateBooking } from '../hooks/useClientPortalQuery'

export default function ClientBookingForm() {
  const navigate = useNavigate()
  const [pickupLocation, setPickupLocation] = useState('')
  const [dropoffLocation, setDropoffLocation] = useState('')
  const [pickupDate, setPickupDate] = useState('')
  const [pickupTime, setPickupTime] = useState('')
  const [passengers, setPassengers] = useState(1)
  const [vehicleType, setVehicleType] = useState('sedan')
  const [loadingQuote, setLoadingQuote] = useState(false)
  const [quote, setQuote] = useState<any>(null)
  const [error, setError] = useState('')

  const createBookingMutation = useCreateBooking()

  const calculateQuote = async () => {
    if (!pickupLocation || !dropoffLocation || !pickupDate || !pickupTime) {
      setError('Please fill in all required fields')
      return
    }

    setLoadingQuote(true)
    setError('')

    try {
      // In production, call pricing API
      // For now, simulate a quote calculation
      const basePrice = 50
      const perPassenger = 10
      const total = basePrice + (passengers * perPassenger)

      setQuote({
        basePrice,
        perPassenger,
        passengers,
        total,
        estimatedDistance: '25 miles',
        estimatedTime: '45 minutes'
      })
    } catch (err: any) {
      setError('Failed to calculate quote')
    } finally {
      setLoadingQuote(false)
    }
  }

  const handleBookingSubmit = () => {
    if (!quote) {
      setError('Please calculate a quote first')
      return
    }

    const bookingData = {
      pickup_location: pickupLocation,
      dropoff_location: dropoffLocation,
      pickup_date: pickupDate,
      pickup_time: pickupTime,
      passengers,
      vehicle_type: vehicleType,
      notes: `Quote calculated: $${quote.total}`
    }

    createBookingMutation.mutate(bookingData, {
      onSuccess: () => {
        navigate('/client/dashboard')
      }
    })
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Create Booking
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Quote Preview Card */}
      {quote && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" color="primary">
              Quote Summary
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Base Price: ${quote.basePrice}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Passengers: {quote.passengers} × ${quote.perPassenger}
            </Typography>
            <Typography variant="h5" sx={{ mt: 1 }}>
              Total: ${quote.total}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Distance: {quote.estimatedDistance} • Time: {quote.estimatedTime}
            </Typography>
          </CardContent>
        </Card>
      )}

      <Paper sx={{ p: 3 }}>
        <Grid container spacing={3}>
          {/* Location Fields */}
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Pickup Location"
              value={pickupLocation}
              onChange={(e) => setPickupLocation(e.target.value)}
              InputProps={{
                startAdornment: <LocationIcon sx={{ mr: 1, color: 'text.secondary' }} />
              }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Dropoff Location"
              value={dropoffLocation}
              onChange={(e) => setDropoffLocation(e.target.value)}
              InputProps={{
                startAdornment: <LocationIcon sx={{ mr: 1, color: 'text.secondary' }} />
              }}
            />
          </Grid>

          {/* Date & Time */}
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Pickup Date"
              type="date"
              value={pickupDate}
              onChange={(e) => setPickupDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
              InputProps={{
                startAdornment: <ScheduleIcon sx={{ mr: 1, color: 'text.secondary' }} />
              }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Pickup Time"
              type="time"
              value={pickupTime}
              onChange={(e) => setPickupTime(e.target.value)}
              InputLabelProps={{ shrink: true }}
              InputProps={{
                startAdornment: <ScheduleIcon sx={{ mr: 1, color: 'text.secondary' }} />
              }}
            />
          </Grid>

          {/* Passengers & Vehicle */}
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Number of Passengers"
              type="number"
              value={passengers}
              onChange={(e) => setPassengers(parseInt(e.target.value) || 1)}
              InputProps={{
                startAdornment: <PeopleIcon sx={{ mr: 1, color: 'text.secondary' }} />
              }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Vehicle Type</InputLabel>
              <Select
                value={vehicleType}
                label="Vehicle Type"
                onChange={(e) => setVehicleType(e.target.value)}
                sx={{ '& .MuiSelect-icon': { mr: 1 } }}
              >
                <MenuItem value="sedan">Sedan</MenuItem>
                <MenuItem value="suv">SUV</MenuItem>
                <MenuItem value="van">Van (6-8 passengers)</MenuItem>
                <MenuItem value="minibus">Minibus (12-15 passengers)</MenuItem>
                <MenuItem value="luxury">Luxury</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {/* Calculate Quote Button */}
          <Grid item xs={12}>
            <Button
              variant="contained"
              startIcon={loadingQuote ? <CircularProgress size={20} /> : <MoneyIcon />}
              onClick={calculateQuote}
              disabled={!pickupLocation || !dropoffLocation || !pickupDate || !pickupTime}
              sx={{ width: '100%' }}
            >
              {loadingQuote ? 'Calculating...' : 'Calculate Quote'}
            </Button>
          </Grid>

          {/* Submit Booking Button */}
          {quote && (
            <Grid item xs={12}>
              <Button
                variant="contained"
                color="success"
                startIcon={<PeopleIcon />}
                onClick={handleBookingSubmit}
                disabled={createBookingMutation.isPending}
                sx={{ width: '100%' }}
              >
                {createBookingMutation.isPending ? 'Creating Booking...' : 'Confirm Booking'}
              </Button>
            </Grid>
          )}
        </Grid>
      </Paper>
    </Box>
  )
}
