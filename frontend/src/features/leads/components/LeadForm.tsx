import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  MenuItem,
  CircularProgress
} from '@mui/material'
import {
  Save as SaveIcon,
  Cancel as CancelIcon,
  ArrowBack as BackIcon
} from '@mui/icons-material'
import { useLead, useCreateLead, useUpdateLead } from '../hooks/useLeads'
import { CreateLeadRequest, UpdateLeadRequest } from '../types/lead.types'

const leadSchema = z.object({
  first_name: z.string().min(1, 'First name is required'),
  last_name: z.string().min(1, 'Last name is required'),
  company_name: z.string().optional(),
  email: z.string().email('Invalid email address'),
  phone: z.string().optional(),
  source: z.string().min(1, 'Source is required'),
  status: z.string().optional(),
  trip_details: z.string().optional(),
  estimated_passengers: z.number().optional().nullable(),
  estimated_trip_date: z.string().optional(),
  pickup_location: z.string().optional(),
  dropoff_location: z.string().optional(),
})

type LeadFormData = z.infer<typeof leadSchema>

export default function LeadForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEditMode = !!id
  
  const { data: lead, isLoading: isLoadingLead } = useLead(Number(id))
  const createMutation = useCreateLead()
  const updateMutation = useUpdateLead()
  
  const {
    control,
    handleSubmit,
    formState: { errors },
    reset
  } = useForm<LeadFormData>({
    resolver: zodResolver(leadSchema),
    defaultValues: {
      first_name: '',
      last_name: '',
      company_name: '',
      email: '',
      phone: '',
      source: 'web',
      status: 'new',
      trip_details: '',
      estimated_passengers: null,
      estimated_trip_date: '',
      pickup_location: '',
      dropoff_location: '',
    }
  })
  
  // Populate form when editing
  useEffect(() => {
    if (lead) {
      reset({
        first_name: lead.first_name,
        last_name: lead.last_name,
        company_name: lead.company_name || '',
        email: lead.email,
        phone: lead.phone || '',
        source: lead.source,
        status: lead.status,
        trip_details: lead.trip_details || '',
        estimated_passengers: lead.estimated_passengers,
        estimated_trip_date: lead.estimated_trip_date || '',
        pickup_location: lead.pickup_location || '',
        dropoff_location: lead.dropoff_location || '',
      })
    }
  }, [lead, reset])
  
  const onSubmit = (data: LeadFormData) => {
    if (isEditMode && id) {
      updateMutation.mutate(
        { id: Number(id), data: data as UpdateLeadRequest },
        {
          onSuccess: () => {
            navigate(`/leads/${id}`)
          }
        }
      )
    } else {
      createMutation.mutate(data as CreateLeadRequest, {
        onSuccess: (newLead) => {
          navigate(`/leads/${newLead.id}`)
        }
      })
    }
  }
  
  if (isEditMode && isLoadingLead) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }
  
  return (
    <Box>
      {/* Header */}
      <Box display="flex" alignItems="center" gap={2} mb={3}>
        <Button
          startIcon={<BackIcon />}
          onClick={() => navigate(isEditMode ? `/leads/${id}` : '/leads')}
        >
          Back
        </Button>
        <Typography variant="h4">
          {isEditMode ? 'Edit Lead' : 'New Lead'}
        </Typography>
      </Box>
      
      {/* Form */}
      <Paper sx={{ p: 3 }}>
        <form onSubmit={handleSubmit(onSubmit)}>
          <Grid container spacing={3}>
            {/* Contact Information */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Contact Information
              </Typography>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Controller
                name="first_name"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="First Name"
                    fullWidth
                    required
                    error={!!errors.first_name}
                    helperText={errors.first_name?.message}
                  />
                )}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Controller
                name="last_name"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Last Name"
                    fullWidth
                    required
                    error={!!errors.last_name}
                    helperText={errors.last_name?.message}
                  />
                )}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Controller
                name="company_name"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Company Name"
                    fullWidth
                    error={!!errors.company_name}
                    helperText={errors.company_name?.message}
                  />
                )}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Controller
                name="email"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Email"
                    type="email"
                    fullWidth
                    required
                    error={!!errors.email}
                    helperText={errors.email?.message}
                  />
                )}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Controller
                name="phone"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Phone"
                    fullWidth
                    error={!!errors.phone}
                    helperText={errors.phone?.message}
                  />
                )}
              />
            </Grid>
            
            {/* Lead Details */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                Lead Details
              </Typography>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Controller
                name="source"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    select
                    label="Source"
                    fullWidth
                    required
                    error={!!errors.source}
                    helperText={errors.source?.message}
                  >
                    <MenuItem value="web">Web</MenuItem>
                    <MenuItem value="phone">Phone</MenuItem>
                    <MenuItem value="email">Email</MenuItem>
                    <MenuItem value="referral">Referral</MenuItem>
                    <MenuItem value="walk_in">Walk In</MenuItem>
                    <MenuItem value="partner">Partner</MenuItem>
                  </TextField>
                )}
              />
            </Grid>
            
            {isEditMode && (
              <Grid item xs={12} md={6}>
                <Controller
                  name="status"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      select
                      label="Status"
                      fullWidth
                      error={!!errors.status}
                      helperText={errors.status?.message}
                    >
                      <MenuItem value="new">New</MenuItem>
                      <MenuItem value="contacted">Contacted</MenuItem>
                      <MenuItem value="qualified">Qualified</MenuItem>
                      <MenuItem value="negotiating">Negotiating</MenuItem>
                      <MenuItem value="converted">Converted</MenuItem>
                      <MenuItem value="dead">Dead</MenuItem>
                    </TextField>
                  )}
                />
              </Grid>
            )}
            
            {/* Trip Information */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                Trip Information (Optional)
              </Typography>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Controller
                name="pickup_location"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Pickup Location"
                    fullWidth
                    error={!!errors.pickup_location}
                    helperText={errors.pickup_location?.message}
                  />
                )}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Controller
                name="dropoff_location"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Dropoff Location"
                    fullWidth
                    error={!!errors.dropoff_location}
                    helperText={errors.dropoff_location?.message}
                  />
                )}
              />
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Controller
                name="estimated_passengers"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Passengers"
                    type="number"
                    fullWidth
                    onChange={(e) => field.onChange(e.target.value ? parseInt(e.target.value) : null)}
                    error={!!errors.estimated_passengers}
                    helperText={errors.estimated_passengers?.message}
                  />
                )}
              />
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Controller
                name="estimated_trip_date"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Trip Date"
                    type="date"
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                    error={!!errors.estimated_trip_date}
                    helperText={errors.estimated_trip_date?.message}
                  />
                )}
              />
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Controller
                name="trip_details"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Trip Details"
                    fullWidth
                    multiline
                    rows={1}
                    error={!!errors.trip_details}
                    helperText={errors.trip_details?.message}
                  />
                )}
              />
            </Grid>
            
            {/* Actions */}
            <Grid item xs={12}>
              <Box display="flex" gap={2} justifyContent="flex-end">
                <Button
                  variant="outlined"
                  startIcon={<CancelIcon />}
                  onClick={() => navigate(isEditMode ? `/leads/${id}` : '/leads')}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  startIcon={<SaveIcon />}
                  disabled={createMutation.isPending || updateMutation.isPending}
                >
                  {createMutation.isPending || updateMutation.isPending
                    ? 'Saving...'
                    : isEditMode
                    ? 'Update Lead'
                    : 'Create Lead'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </form>
      </Paper>
    </Box>
  )
}
