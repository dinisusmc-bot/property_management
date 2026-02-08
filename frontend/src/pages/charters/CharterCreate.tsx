import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Typography,
  Paper,
  Box,
  TextField,
  Button,
  Grid,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  CircularProgress,
  Checkbox,
  FormControlLabel,
  IconButton,
  Radio,
  RadioGroup
} from '@mui/material'
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material'
import api from '../../services/api'
import { PricingCalculator } from '../../features/pricing/components/PricingCalculator'
import { AmenitySelector } from '../../features/pricing/components/AmenitySelector'
import { PromoCodeInput } from '../../features/pricing/components/PromoCodeInput'
import { DOTComplianceCheck } from '../../features/pricing/components/DOTComplianceCheck'
import { PricingRequest, PricingResponse, PromoCode, DOTCompliance } from '../../features/pricing/types/pricing.types'

interface Client {
  id: number
  name: string
}

interface Vehicle {
  id: number
  name: string
  capacity: number
  base_rate: number
  per_mile_rate: number
}

interface Stop {
  sequence: number
  location: string
  arrival_time: string
  departure_time: string
  notes: string
}

interface CharterFormData {
  client_id: number | ''
  vehicle_id: number | ''
  trip_date: string
  passengers: number
  trip_hours: number
  trip_days: number
  estimated_miles: number
  pickup_location: string
  dropoff_location: string
  trip_type: 'point_to_point' | 'hourly' | 'airport' | 'multi_day'
  is_overnight: boolean
  is_weekend: boolean
  is_holiday: boolean
  driver_gratuity_percent: number
  fuel_surcharge_percent: number
  base_cost: number
  mileage_cost: number
  additional_fees: number
  notes: string
}

export default function CharterCreate() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [clients, setClients] = useState<Client[]>([])
  const [vehicles, setVehicles] = useState<Vehicle[]>([])
  const [loadingData, setLoadingData] = useState(true)
  
  const [formData, setFormData] = useState<CharterFormData>({
    client_id: '',
    vehicle_id: '',
    trip_date: '',
    passengers: 1,
    trip_hours: 4,
    trip_days: 1,
    estimated_miles: 50,
    pickup_location: '',
    dropoff_location: '',
    trip_type: 'point_to_point',
    is_overnight: false,
    is_weekend: false,
    is_holiday: false,
    driver_gratuity_percent: 18,
    fuel_surcharge_percent: 5,
    base_cost: 0,
    mileage_cost: 0,
    additional_fees: 0,
    notes: ''
  })

  const [stops, setStops] = useState<Stop[]>([])
  const [errors, setErrors] = useState<Partial<Record<keyof CharterFormData, string>>>({})
  
  // Pricing state
  const [selectedAmenities, setSelectedAmenities] = useState<string[]>([])
  const [appliedPromoCode, setAppliedPromoCode] = useState<PromoCode | null>(null)
  const [pricingResponse, setPricingResponse] = useState<PricingResponse | null>(null)
  const [dotCompliance, setDotCompliance] = useState<DOTCompliance | null>(null)

  useEffect(() => {
    fetchInitialData()
  }, [])

  const fetchInitialData = async () => {
    const maxAttempts = 3
    const retryDelayMs = 750

    setLoadingData(true)
    setError('')

    for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
      try {
        const [clientsRes, vehiclesRes] = await Promise.all([
          api.get('/api/v1/clients', { headers: { Authorization: null } }),
          api.get('/api/v1/vehicles', { headers: { Authorization: null } })
        ])

        setClients(clientsRes.data)
        setVehicles(vehiclesRes.data)
        setLoadingData(false)
        return
      } catch (err: any) {
        if (attempt === maxAttempts) {
          setError('Failed to load clients and vehicles')
          setLoadingData(false)
          return
        }

        await new Promise(resolve => setTimeout(resolve, retryDelayMs))
      }
    }
  }

  // Build pricing request from form data
  const buildPricingRequest = (): PricingRequest | null => {
    if (!formData.client_id || !formData.vehicle_id || !formData.trip_date) {
      return null
    }

    return {
      client_id: Number(formData.client_id),
      vehicle_id: Number(formData.vehicle_id),
      passengers: formData.passengers,
      trip_date: formData.trip_date,
      total_miles: Math.max(0, formData.estimated_miles || 0),
      trip_hours: Math.max(0.5, formData.trip_hours || 0),
      is_overnight: formData.is_overnight,
      is_weekend: formData.is_weekend,
      is_holiday: formData.is_holiday,
      additional_fees: 0,
      notes: formData.notes || undefined,
    }
  }

  const handlePricingCalculated = (pricing: PricingResponse) => {
    setPricingResponse(pricing)
    const breakdown = pricing.breakdown
    const additionalFees =
      breakdown.additional_fees +
      breakdown.time_based_cost +
      breakdown.fuel_surcharge

    setFormData(prev => ({
      ...prev,
      base_cost: breakdown.base_cost,
      mileage_cost: breakdown.mileage_cost,
      additional_fees: additionalFees
    }))
  }

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof CharterFormData, string>> = {}

    if (!formData.client_id) {
      newErrors.client_id = 'Client is required'
    }

    if (!formData.vehicle_id) {
      newErrors.vehicle_id = 'Vehicle is required'
    }

    if (!formData.trip_date) {
      newErrors.trip_date = 'Trip date is required'
    }

    if (!formData.pickup_location) {
      newErrors.pickup_location = 'Pickup location is required'
    }

    if (formData.passengers < 1) {
      newErrors.passengers = 'At least 1 passenger required'
    }

    if (formData.trip_hours < 0.5) {
      newErrors.trip_hours = 'Minimum trip duration is 0.5 hours'
    }

    if (dotCompliance && !dotCompliance.compliant) {
      newErrors.trip_hours = 'Trip duration exceeds DOT compliance limits'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    try {
      setLoading(true)
      setError('')
      
      const totalCost = pricingResponse ? pricingResponse.breakdown.total_cost : 
        (formData.base_cost + formData.mileage_cost + formData.additional_fees)
      
      const charterData = {
        ...formData,
        total_cost: totalCost,
        status: 'quote',
        amenities: selectedAmenities,
        promo_code: appliedPromoCode?.code,
        stops: stops.map(stop => ({
          location: stop.location,
          arrival_time: stop.arrival_time || null,
          departure_time: stop.departure_time || null,
          notes: stop.notes
        }))
      }
      
      const response = await api.post('/api/v1/charters', charterData)
      
      navigate(`/charters/${response.data.id}`)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create charter')
      setLoading(false)
    }
  }

  const handleChange = (field: keyof CharterFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }))
    }
  }

  const addStop = () => {
    setStops(prev => [...prev, { 
      sequence: prev.length + 1, 
      location: '', 
      arrival_time: '',
      departure_time: '',
      notes: '' 
    }])
  }

  const removeStop = (index: number) => {
    setStops(prev => prev.filter((_, i) => i !== index).map((stop, i) => ({ ...stop, sequence: i + 1 })))
  }

  const updateStop = (index: number, field: keyof Stop, value: string | number) => {
    setStops(prev => prev.map((stop, i) => i === index ? { ...stop, [field]: value } : stop))
  }

  const pricingRequest = buildPricingRequest()

  if (loadingData) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Create Charter Quote
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <form onSubmit={handleSubmit}>
        <Grid container spacing={3}>
          {/* Left Column - Charter Details */}
          <Grid item xs={12} lg={7}>
            <Paper sx={{ p: 3, mb: 3 }}>
              {/* Client and Vehicle Selection */}
              <Typography variant="h6" gutterBottom>Booking Details</Typography>

              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth required error={!!errors.client_id}>
                    <InputLabel>Client</InputLabel>
                    <Select
                      value={formData.client_id}
                      label="Client"
                      onChange={(e) => handleChange('client_id', e.target.value)}
                    >
                      {clients.map((client) => (
                        <MenuItem key={client.id} value={client.id}>
                          {client.name}
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.client_id && <Typography color="error" variant="caption">{errors.client_id}</Typography>}
                  </FormControl>
                </Grid>

                <Grid item xs={12} md={6}>
                  <FormControl fullWidth required error={!!errors.vehicle_id}>
                    <InputLabel>Vehicle</InputLabel>
                    <Select
                      value={formData.vehicle_id}
                      label="Vehicle"
                      onChange={(e) => handleChange('vehicle_id', e.target.value)}
                    >
                      {vehicles.map((vehicle) => (
                        <MenuItem key={vehicle.id} value={vehicle.id}>
                          {vehicle.name} (Capacity: {vehicle.capacity})
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.vehicle_id && <Typography color="error" variant="caption">{errors.vehicle_id}</Typography>}
                  </FormControl>
                </Grid>
              </Grid>
            </Paper>

            <Paper sx={{ p: 3, mb: 3 }}>
              {/* Trip Type */}
              <Typography variant="h6" gutterBottom>Trip Type</Typography>

              <FormControl component="fieldset" sx={{ mb: 2 }}>
                <RadioGroup
                  row
                  value={formData.trip_type}
                  onChange={(e) => handleChange('trip_type', e.target.value)}
                >
                  <FormControlLabel value="point_to_point" control={<Radio />} label="Point to Point" />
                  <FormControlLabel value="hourly" control={<Radio />} label="Hourly" />
                  <FormControlLabel value="airport" control={<Radio />} label="Airport" />
                  <FormControlLabel value="multi_day" control={<Radio />} label="Multi-Day" />
                </RadioGroup>
              </FormControl>

              {/* Trip Information */}
              <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>Trip Details</Typography>

              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    required
                    type="date"
                    label="Trip Date"
                    value={formData.trip_date}
                    onChange={(e) => handleChange('trip_date', e.target.value)}
                    error={!!errors.trip_date}
                    helperText={errors.trip_date}
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    required
                    type="number"
                    label="Number of Passengers"
                    value={formData.passengers}
                    onChange={(e) => handleChange('passengers', parseInt(e.target.value) || 0)}
                    error={!!errors.passengers}
                    helperText={errors.passengers}
                    InputProps={{ inputProps: { min: 1 } }}
                  />
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    required
                    label="Pickup Location"
                    value={formData.pickup_location}
                    onChange={(e) => handleChange('pickup_location', e.target.value)}
                    error={!!errors.pickup_location}
                    helperText={errors.pickup_location}
                    placeholder="123 Main St, City, State"
                  />
                </Grid>

                {formData.trip_type !== 'hourly' && (
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Dropoff Location"
                      value={formData.dropoff_location}
                      onChange={(e) => handleChange('dropoff_location', e.target.value)}
                      placeholder="456 Oak Ave, City, State"
                    />
                  </Grid>
                )}

                {(formData.trip_type === 'hourly' || formData.trip_type === 'multi_day') && (
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      required
                      type="number"
                      label="Trip Duration (hours)"
                      value={formData.trip_hours}
                      onChange={(e) => handleChange('trip_hours', parseFloat(e.target.value) || 0)}
                      error={!!errors.trip_hours}
                      helperText={errors.trip_hours}
                      InputProps={{ inputProps: { min: 0.5, step: 0.5 } }}
                    />
                  </Grid>
                )}

                {formData.trip_type === 'multi_day' && (
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      required
                      type="number"
                      label="Number of Days"
                      value={formData.trip_days}
                      onChange={(e) => handleChange('trip_days', parseInt(e.target.value) || 0)}
                      InputProps={{ inputProps: { min: 1 } }}
                    />
                  </Grid>
                )}

                {formData.trip_type !== 'hourly' && (
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Estimated Miles"
                      value={formData.estimated_miles}
                      onChange={(e) => handleChange('estimated_miles', parseInt(e.target.value) || 0)}
                      InputProps={{ inputProps: { min: 0 } }}
                    />
                  </Grid>
                )}

                <Grid item xs={12} md={4}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={formData.is_overnight}
                        onChange={(e) => handleChange('is_overnight', e.target.checked)}
                      />
                    }
                    label="Overnight Trip"
                  />
                </Grid>

                <Grid item xs={12} md={4}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={formData.is_weekend}
                        onChange={(e) => handleChange('is_weekend', e.target.checked)}
                      />
                    }
                    label="Weekend Service"
                  />
                </Grid>

                <Grid item xs={12} md={4}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={formData.is_holiday}
                        onChange={(e) => handleChange('is_holiday', e.target.checked)}
                      />
                    }
                    label="Holiday"
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Driver Gratuity %"
                    value={formData.driver_gratuity_percent}
                    onChange={(e) => handleChange('driver_gratuity_percent', parseFloat(e.target.value) || 0)}
                    InputProps={{ inputProps: { min: 0, max: 100, step: 1 } }}
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Fuel Surcharge %"
                    value={formData.fuel_surcharge_percent}
                    onChange={(e) => handleChange('fuel_surcharge_percent', parseFloat(e.target.value) || 0)}
                    InputProps={{ inputProps: { min: 0, max: 100, step: 0.5 } }}
                  />
                </Grid>
              </Grid>
            </Paper>

            {/* Amenities */}
            <Box sx={{ mb: 3 }}>
              <AmenitySelector
                selectedAmenities={selectedAmenities}
                onChange={setSelectedAmenities}
              />
            </Box>

            {/* Stops */}
            <Paper sx={{ p: 3, mb: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ flexGrow: 1 }}>Stops (Optional)</Typography>
                <Button
                  startIcon={<AddIcon />}
                  onClick={addStop}
                  variant="outlined"
                  size="small"
                >
                  Add Stop
                </Button>
              </Box>

              {stops.map((stop, index) => (
                <Paper key={index} variant="outlined" sx={{ p: 2, mb: 2 }}>
                  <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} md={4}>
                      <TextField
                        fullWidth
                        label={`Stop ${stop.sequence} - Location`}
                        value={stop.location}
                        onChange={(e) => updateStop(index, 'location', e.target.value)}
                        placeholder="123 Main St, City, State"
                        size="small"
                      />
                    </Grid>
                    <Grid item xs={12} md={2}>
                      <TextField
                        fullWidth
                        type="time"
                        label="Arrival Time"
                        value={stop.arrival_time}
                        onChange={(e) => updateStop(index, 'arrival_time', e.target.value)}
                        InputLabelProps={{ shrink: true }}
                        size="small"
                      />
                    </Grid>
                    <Grid item xs={12} md={2}>
                      <TextField
                        fullWidth
                        type="time"
                        label="Departure Time"
                        value={stop.departure_time}
                        onChange={(e) => updateStop(index, 'departure_time', e.target.value)}
                        InputLabelProps={{ shrink: true }}
                        size="small"
                      />
                    </Grid>
                    <Grid item xs={12} md={3}>
                      <TextField
                        fullWidth
                        label="Notes"
                        value={stop.notes}
                        onChange={(e) => updateStop(index, 'notes', e.target.value)}
                        placeholder="Instructions"
                        size="small"
                      />
                    </Grid>
                    <Grid item xs={12} md={1}>
                      <IconButton onClick={() => removeStop(index)} color="error">
                        <DeleteIcon />
                      </IconButton>
                    </Grid>
                  </Grid>
                </Paper>
              ))}

              {stops.length === 0 && (
                <Typography color="text.secondary" variant="body2">
                  No stops added
                </Typography>
              )}
            </Paper>

            {/* Notes */}
            <Paper sx={{ p: 3 }}>
              <TextField
                fullWidth
                multiline
                rows={4}
                label="Special Requirements / Notes"
                value={formData.notes}
                onChange={(e) => handleChange('notes', e.target.value)}
                placeholder="Any special requests, requirements, or additional information..."
              />
            </Paper>
          </Grid>

          {/* Right Column - Pricing */}
          <Grid item xs={12} lg={5}>
            {/* DOT Compliance */}
            <Box sx={{ mb: 3 }}>
              <DOTComplianceCheck
                distanceMiles={formData.estimated_miles}
                stopsCount={stops.length}
                tripHours={formData.trip_hours}
                isMultiDay={formData.trip_days > 1}
                onComplianceChecked={setDotCompliance}
              />
            </Box>

            {/* Promo Code */}
            {pricingResponse && (
              <Box sx={{ mb: 3 }}>
                <PromoCodeInput
                  amount={pricingResponse.breakdown.subtotal}
                  onPromoCodeApplied={setAppliedPromoCode}
                  currentPromoCode={appliedPromoCode?.code}
                />
              </Box>
            )}

            {/* Pricing Calculator */}
            {pricingRequest && (
              <Box sx={{ mb: 3 }}>
                <PricingCalculator
                  request={pricingRequest}
                  onPricingCalculated={handlePricingCalculated}
                />
              </Box>
            )}

            {!pricingRequest && (
              <Paper sx={{ p: 3, mb: 3 }}>
                <Alert severity="info">
                  Fill in the trip details to see pricing
                </Alert>
              </Paper>
            )}

            {/* Actions */}
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', gap: 2, flexDirection: 'column' }}>
                <Button
                  type="submit"
                  variant="contained"
                  size="large"
                  fullWidth
                  disabled={loading || !pricingRequest}
                >
                  {loading ? <CircularProgress size={24} /> : 'Create Charter Quote'}
                </Button>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => navigate('/charters')}
                  disabled={loading}
                >
                  Cancel
                </Button>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </form>
    </Box>
  )
}
