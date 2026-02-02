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
  Divider
} from '@mui/material'
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material'
import api from '../../services/api'

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
  is_overnight: boolean
  is_weekend: boolean
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
    trip_hours: 1,
    is_overnight: false,
    is_weekend: false,
    base_cost: 0,
    mileage_cost: 0,
    additional_fees: 0,
    notes: ''
  })

  const [stops, setStops] = useState<Stop[]>([])
  const [errors, setErrors] = useState<Partial<Record<keyof CharterFormData, string>>>({})

  useEffect(() => {
    fetchInitialData()
  }, [])

  useEffect(() => {
    // Auto-calculate costs when vehicle changes
    if (formData.vehicle_id) {
      const vehicle = vehicles.find(v => v.id === formData.vehicle_id)
      if (vehicle) {
        setFormData(prev => ({
          ...prev,
          base_cost: vehicle.base_rate * prev.trip_hours,
          mileage_cost: vehicle.per_mile_rate * 50 // Default 50 miles, user can adjust
        }))
      }
    }
  }, [formData.vehicle_id, formData.trip_hours, vehicles])

  const fetchInitialData = async () => {
    try {
      setLoadingData(true)
      const [clientsRes, vehiclesRes] = await Promise.all([
        api.get('/api/v1/clients/clients'),
        api.get('/api/v1/charters/vehicles')
      ])
      setClients(clientsRes.data)
      setVehicles(vehiclesRes.data)
    } catch (err: any) {
      setError('Failed to load clients and vehicles')
    } finally {
      setLoadingData(false)
    }
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

    if (formData.passengers < 1) {
      newErrors.passengers = 'At least 1 passenger required'
    }

    if (formData.trip_hours < 0.5) {
      newErrors.trip_hours = 'Minimum trip duration is 0.5 hours'
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
      
      const totalCost = formData.base_cost + formData.mileage_cost + formData.additional_fees
      
      const charterData = {
        ...formData,
        total_cost: totalCost,
        status: 'quote',
        stops: stops.map(stop => ({
          location: stop.location,
          arrival_time: stop.arrival_time || null,
          departure_time: stop.departure_time || null,
          notes: stop.notes
        }))
      }
      
      const response = await api.post('/api/v1/charters/charters', charterData)
      
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

  const totalCost = formData.base_cost + formData.mileage_cost + formData.additional_fees

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
        Create Charter
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Paper sx={{ p: 3 }}>
        <form onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            {/* Client and Vehicle Selection */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>Booking Details</Typography>
            </Grid>

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

            {/* Trip Information */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>Trip Information</Typography>
            </Grid>

            <Grid item xs={12} md={4}>
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

            <Grid item xs={12} md={4}>
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

            <Grid item xs={12} md={4}>
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
            </Grid>

            <Grid item xs={12} md={6}>
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

            {/* Pricing */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>Pricing</Typography>
            </Grid>

            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                type="number"
                label="Base Cost"
                value={formData.base_cost}
                onChange={(e) => handleChange('base_cost', parseFloat(e.target.value) || 0)}
                InputProps={{ inputProps: { min: 0, step: 0.01 } }}
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                type="number"
                label="Mileage Cost"
                value={formData.mileage_cost}
                onChange={(e) => handleChange('mileage_cost', parseFloat(e.target.value) || 0)}
                InputProps={{ inputProps: { min: 0, step: 0.01 } }}
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                type="number"
                label="Additional Fees"
                value={formData.additional_fees}
                onChange={(e) => handleChange('additional_fees', parseFloat(e.target.value) || 0)}
                InputProps={{ inputProps: { min: 0, step: 0.01 } }}
              />
            </Grid>

            <Grid item xs={12}>
              <Alert severity="info">
                <Typography variant="h6">Total Cost: ${totalCost.toFixed(2)}</Typography>
              </Alert>
            </Grid>

            {/* Stops */}
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 2, mb: 1 }}>
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
              <Divider />
            </Grid>

            {stops.map((stop, index) => (
              <Grid item xs={12} key={index}>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} md={4}>
                      <TextField
                        fullWidth
                        label={`Stop ${stop.sequence} - Location`}
                        value={stop.location}
                        onChange={(e) => updateStop(index, 'location', e.target.value)}
                        placeholder="123 Main St, City, State"
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
                      />
                    </Grid>
                    <Grid item xs={12} md={3}>
                      <TextField
                        fullWidth
                        label="Notes"
                        value={stop.notes}
                        onChange={(e) => updateStop(index, 'notes', e.target.value)}
                        placeholder="Pickup/dropoff instructions"
                      />
                    </Grid>
                    <Grid item xs={12} md={1}>
                      <IconButton onClick={() => removeStop(index)} color="error">
                        <DeleteIcon />
                      </IconButton>
                    </Grid>
                  </Grid>
                </Paper>
              </Grid>
            ))}

            {/* Notes */}
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={4}
                label="Special Requirements / Notes"
                value={formData.notes}
                onChange={(e) => handleChange('notes', e.target.value)}
                placeholder="Any special requests, requirements, or additional information..."
              />
            </Grid>

            {/* Actions */}
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', mt: 2 }}>
                <Button
                  variant="outlined"
                  onClick={() => navigate('/charters')}
                  disabled={loading}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={loading}
                >
                  {loading ? <CircularProgress size={24} /> : 'Create Charter'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </form>
      </Paper>
    </Box>
  )
}
