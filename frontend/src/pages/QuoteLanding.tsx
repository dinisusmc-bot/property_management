import { useState } from 'react'
import {
  Box,
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Stepper,
  Step,
  StepLabel,
  Grid,
  IconButton,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  InputAdornment,
  Checkbox,
  FormControlLabel,
  Divider
} from '@mui/material'
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  DirectionsBus as BusIcon,
  Event as EventIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  LocationOn as LocationIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material'
import axios from 'axios'

interface Stop {
  location: string
  arrival_time: string
  departure_time: string
  notes: string
}

interface QuoteFormData {
  // Step 1: Trip Details
  trip_date: string
  passengers: number
  trip_hours: number
  is_overnight: boolean
  is_weekend: boolean

  // Step 2: Vehicle Selection
  vehicle_id: number | ''

  // Step 3: Itinerary
  stops: Stop[]

  // Step 4: Contact Info
  contact_name: string
  contact_email: string
  contact_phone: string
  company_name: string
  notes: string
}

const steps = ['Trip Details', 'Select Vehicle', 'Itinerary', 'Contact Information']

export default function QuoteLanding() {
  const [activeStep, setActiveStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [submittedQuoteId, setSubmittedQuoteId] = useState<number | null>(null)

  const [formData, setFormData] = useState<QuoteFormData>({
    trip_date: '',
    passengers: 1,
    trip_hours: 1,
    is_overnight: false,
    is_weekend: false,
    vehicle_id: '',
    stops: [
      { location: '', arrival_time: '', departure_time: '', notes: '' },
      { location: '', arrival_time: '', departure_time: '', notes: '' }
    ],
    contact_name: '',
    contact_email: '',
    contact_phone: '',
    company_name: '',
    notes: ''
  })

  const [vehicles] = useState([
    { id: 1, name: 'Luxury Coach (55 passengers)', capacity: 55, base_rate: 150, per_mile_rate: 3.5 },
    { id: 2, name: 'Executive Minibus (30 passengers)', capacity: 30, base_rate: 120, per_mile_rate: 2.8 },
    { id: 3, name: 'Shuttle Van (15 passengers)', capacity: 15, base_rate: 80, per_mile_rate: 2.0 }
  ])

  const handleNext = () => {
    if (validateStep(activeStep)) {
      setActiveStep((prevStep) => prevStep + 1)
      setError(null)
    }
  }

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1)
    setError(null)
  }

  const validateStep = (step: number): boolean => {
    switch (step) {
      case 0: // Trip Details
        if (!formData.trip_date) {
          setError('Please select a trip date')
          return false
        }
        if (formData.passengers < 1) {
          setError('Number of passengers must be at least 1')
          return false
        }
        if (formData.trip_hours < 0.5) {
          setError('Trip hours must be at least 0.5')
          return false
        }
        return true
      
      case 1: // Vehicle Selection
        if (!formData.vehicle_id) {
          setError('Please select a vehicle')
          return false
        }
        return true
      
      case 2: // Itinerary
        if (formData.stops.length < 2) {
          setError('Please add at least 2 stops (pickup and dropoff)')
          return false
        }
        for (let i = 0; i < formData.stops.length; i++) {
          if (!formData.stops[i].location.trim()) {
            setError(`Please enter a location for stop ${i + 1}`)
            return false
          }
        }
        return true
      
      case 3: // Contact Info
        if (!formData.contact_name.trim()) {
          setError('Please enter your name')
          return false
        }
        if (!formData.contact_email.trim()) {
          setError('Please enter your email')
          return false
        }
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.contact_email)) {
          setError('Please enter a valid email address')
          return false
        }
        return true
      
      default:
        return true
    }
  }

  const handleSubmit = async () => {
    if (!validateStep(3)) return

    setLoading(true)
    setError(null)

    try {
      // Calculate estimated cost (simple calculation for demo)
      const selectedVehicle = vehicles.find(v => v.id === formData.vehicle_id)
      const estimatedMiles = formData.trip_hours * 50 // rough estimate
      const base_cost = selectedVehicle ? selectedVehicle.base_rate * formData.trip_hours : 0
      const mileage_cost = selectedVehicle ? selectedVehicle.per_mile_rate * estimatedMiles : 0
      const additional_fees = formData.is_overnight ? 200 : 0
      const total_cost = base_cost + mileage_cost + additional_fees

      const quotePayload = {
        client_id: 1, // Temporary client ID for quotes
        vehicle_id: formData.vehicle_id,
        trip_date: formData.trip_date,
        passengers: formData.passengers,
        trip_hours: formData.trip_hours,
        is_overnight: formData.is_overnight,
        is_weekend: formData.is_weekend,
        base_cost,
        mileage_cost,
        additional_fees,
        total_cost,
        status: 'quote',
        notes: `Contact: ${formData.contact_name} (${formData.contact_email}, ${formData.contact_phone})\nCompany: ${formData.company_name}\n\nAdditional Notes: ${formData.notes}`,
        stops: formData.stops.map((stop, idx) => ({
          sequence: idx,
          location: stop.location,
          arrival_time: stop.arrival_time || null,
          departure_time: stop.departure_time || null,
          notes: stop.notes || null
        }))
      }

      const response = await axios.post(
        'http://localhost:8080/api/v1/charters/quotes/submit',
        quotePayload
      )

      setSubmittedQuoteId(response.data.id)
      setSuccess(true)
      setLoading(false)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit quote request. Please try again.')
      setLoading(false)
    }
  }

  const handleChange = (field: keyof QuoteFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    setError(null)
  }

  const addStop = () => {
    setFormData(prev => ({
      ...prev,
      stops: [...prev.stops, { location: '', arrival_time: '', departure_time: '', notes: '' }]
    }))
  }

  const removeStop = (index: number) => {
    if (formData.stops.length > 2) {
      setFormData(prev => ({
        ...prev,
        stops: prev.stops.filter((_, i) => i !== index)
      }))
    }
  }

  const updateStop = (index: number, field: keyof Stop, value: string) => {
    setFormData(prev => ({
      ...prev,
      stops: prev.stops.map((stop, i) => 
        i === index ? { ...stop, [field]: value } : stop
      )
    }))
  }

  if (success) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          bgcolor: 'grey.50',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          p: 3
        }}
      >
        <Container maxWidth="md">
          <Paper sx={{ p: 6, textAlign: 'center', boxShadow: 4 }}>
            <CheckCircleIcon sx={{ fontSize: 80, color: '#4caf50', mb: 2 }} />
            <Typography variant="h3" gutterBottom fontWeight="bold" color="primary">
              Quote Request Received!
            </Typography>
            <Typography variant="h6" color="text.secondary" paragraph>
              Thank you for choosing our charter services.
            </Typography>
            <Box sx={{ bgcolor: 'grey.100', p: 3, borderRadius: 2, my: 3 }}>
              <Typography variant="body1" paragraph sx={{ mb: 1 }}>
                Your Quote Reference Number:
              </Typography>
              <Typography variant="h4" fontWeight="bold" color="primary">
                #{submittedQuoteId}
              </Typography>
            </Box>
            <Typography variant="body1" color="text.secondary" paragraph>
              Our team will review your request and send you a detailed quote within 24 hours.
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              A confirmation has been sent to <strong>{formData.contact_email}</strong>
            </Typography>
            <Box sx={{ mt: 4, display: 'flex', gap: 2, justifyContent: 'center' }}>
              <Button
                variant="contained"
                size="large"
                onClick={() => window.location.href = '/'}
                sx={{ 
                  px: 4,
                  bgcolor: 'primary.main',
                  '&:hover': { bgcolor: 'primary.dark' }
                }}
              >
                Return to Home
              </Button>
              <Button
                variant="outlined"
                size="large"
                onClick={() => window.location.href = '/quote'}
                sx={{ px: 4 }}
              >
                Request Another Quote
              </Button>
            </Box>
          </Paper>
        </Container>
      </Box>
    )
  }

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                <EventIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
                When do you need the charter?
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Trip Date"
                type="date"
                value={formData.trip_date}
                onChange={(e) => handleChange('trip_date', e.target.value)}
                InputLabelProps={{ shrink: true }}
                inputProps={{ min: new Date().toISOString().split('T')[0] }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Number of Passengers"
                type="number"
                value={formData.passengers}
                onChange={(e) => handleChange('passengers', parseInt(e.target.value))}
                InputProps={{
                  startAdornment: <InputAdornment position="start">👥</InputAdornment>
                }}
                inputProps={{ min: 1, max: 100 }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Estimated Trip Duration (hours)"
                type="number"
                value={formData.trip_hours}
                onChange={(e) => handleChange('trip_hours', parseFloat(e.target.value))}
                InputProps={{
                  startAdornment: <InputAdornment position="start">⏱️</InputAdornment>
                }}
                inputProps={{ min: 0.5, step: 0.5 }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.is_overnight}
                    onChange={(e) => handleChange('is_overnight', e.target.checked)}
                  />
                }
                label="Overnight Trip"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.is_weekend}
                    onChange={(e) => handleChange('is_weekend', e.target.checked)}
                  />
                }
                label="Weekend Trip"
              />
            </Grid>
          </Grid>
        )

      case 1:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                <BusIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
                Select Your Vehicle
              </Typography>
            </Grid>
            {vehicles.map((vehicle) => (
              <Grid item xs={12} md={4} key={vehicle.id}>
                <Card
                  sx={{
                    cursor: 'pointer',
                    border: formData.vehicle_id === vehicle.id ? 3 : 1,
                    borderColor: formData.vehicle_id === vehicle.id ? 'primary.main' : 'divider',
                    '&:hover': { borderColor: 'primary.main' }
                  }}
                  onClick={() => handleChange('vehicle_id', vehicle.id)}
                >
                  <CardContent>
                    <BusIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                    <Typography variant="h6" gutterBottom>
                      {vehicle.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Capacity: {vehicle.capacity} passengers
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Base Rate: ${vehicle.base_rate}/hour
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Per Mile: ${vehicle.per_mile_rate}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
            {formData.passengers > 0 && (
              <Grid item xs={12}>
                <Alert severity="info">
                  Based on {formData.passengers} passengers, we recommend vehicles with at least that capacity.
                </Alert>
              </Grid>
            )}
          </Grid>
        )

      case 2:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                <LocationIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
                Trip Itinerary
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Add your pickup location, destination, and any stops along the way
              </Typography>
            </Grid>
            {formData.stops.map((stop, index) => (
              <Grid item xs={12} key={index}>
                <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                    <Typography variant="subtitle1" fontWeight="bold">
                      Stop {index + 1} {index === 0 ? '(Pickup)' : index === formData.stops.length - 1 ? '(Drop-off)' : '(Waypoint)'}
                    </Typography>
                    {formData.stops.length > 2 && (
                      <IconButton size="small" onClick={() => removeStop(index)} color="error">
                        <DeleteIcon />
                      </IconButton>
                    )}
                  </Box>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Location Address"
                        value={stop.location}
                        onChange={(e) => updateStop(index, 'location', e.target.value)}
                        placeholder="e.g., 123 Main St, New York, NY 10001"
                        InputProps={{
                          startAdornment: <InputAdornment position="start"><LocationIcon /></InputAdornment>
                        }}
                      />
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Arrival Time (Optional)"
                        type="time"
                        value={stop.arrival_time}
                        onChange={(e) => updateStop(index, 'arrival_time', e.target.value)}
                        InputLabelProps={{ shrink: true }}
                      />
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Departure Time (Optional)"
                        type="time"
                        value={stop.departure_time}
                        onChange={(e) => updateStop(index, 'departure_time', e.target.value)}
                        InputLabelProps={{ shrink: true }}
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Notes (Optional)"
                        value={stop.notes}
                        onChange={(e) => updateStop(index, 'notes', e.target.value)}
                        placeholder="Special instructions for this stop"
                        multiline
                        rows={2}
                      />
                    </Grid>
                  </Grid>
                </Paper>
              </Grid>
            ))}
            <Grid item xs={12}>
              <Button
                variant="outlined"
                startIcon={<AddIcon />}
                onClick={addStop}
                fullWidth
              >
                Add Another Stop
              </Button>
            </Grid>
          </Grid>
        )

      case 3:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Contact Information
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                We'll use this information to send you the quote
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Your Name"
                value={formData.contact_name}
                onChange={(e) => handleChange('contact_name', e.target.value)}
                InputProps={{
                  startAdornment: <InputAdornment position="start">👤</InputAdornment>
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Company Name (Optional)"
                value={formData.company_name}
                onChange={(e) => handleChange('company_name', e.target.value)}
                InputProps={{
                  startAdornment: <InputAdornment position="start">🏢</InputAdornment>
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Email Address"
                type="email"
                value={formData.contact_email}
                onChange={(e) => handleChange('contact_email', e.target.value)}
                InputProps={{
                  startAdornment: <InputAdornment position="start"><EmailIcon /></InputAdornment>
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Phone Number"
                value={formData.contact_phone}
                onChange={(e) => handleChange('contact_phone', e.target.value)}
                InputProps={{
                  startAdornment: <InputAdornment position="start"><PhoneIcon /></InputAdornment>
                }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Additional Notes (Optional)"
                value={formData.notes}
                onChange={(e) => handleChange('notes', e.target.value)}
                multiline
                rows={4}
                placeholder="Any special requirements or additional information..."
              />
            </Grid>
          </Grid>
        )

      default:
        return null
    }
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        bgcolor: 'grey.50',
        py: 4
      }}
    >
      <Container maxWidth="lg">
        {/* Header */}
        <Paper sx={{ p: 4, mb: 4, textAlign: 'center', bgcolor: 'primary.main', color: 'white' }}>
          <Typography variant="h3" gutterBottom fontWeight="bold">
            Instant Quick Quote
          </Typography>
          <Typography variant="h6" sx={{ fontWeight: 300 }}>
            Get your personalized charter bus quote in minutes - Available 24/7
          </Typography>
        </Paper>

        {/* Stepper Form */}
        <Paper sx={{ p: 4, boxShadow: 3 }}>
          <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <Box sx={{ mt: 4 }}>
            {renderStepContent(activeStep)}
          </Box>

          <Divider sx={{ my: 4 }} />

          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Button
              disabled={activeStep === 0}
              onClick={handleBack}
              variant="outlined"
              size="large"
            >
              Back
            </Button>
            <Box sx={{ flex: '1 1 auto' }} />
            {activeStep === steps.length - 1 ? (
              <Button
                variant="contained"
                onClick={handleSubmit}
                disabled={loading}
                size="large"
                sx={{
                  bgcolor: '#4caf50',
                  '&:hover': { bgcolor: '#45a049' },
                  px: 4
                }}
              >
                {loading ? <CircularProgress size={24} /> : 'Get My Quote Now'}
              </Button>
            ) : (
              <Button 
                variant="contained" 
                onClick={handleNext} 
                size="large"
                sx={{ px: 4 }}
              >
                Continue
              </Button>
            )}
          </Box>
        </Paper>

        {/* Trust Badges */}
        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            🛡️ Safe & Reliable • 💰 Competitive Pricing • ⏰ 24/7 Availability • 🚌 Nationwide Service
          </Typography>
        </Box>
      </Container>
    </Box>
  )
}
