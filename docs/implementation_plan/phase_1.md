# Phase 1: Sales Agent Core Features
## Duration: 4 weeks | Priority: Critical

[← Back to Implementation Plan](README.md)

---

## Overview

**Goal**: Implement essential sales agent workflows including lead management, advanced quote builder, agent dashboard, and charter cloning capabilities.

**Business Impact**: High - These features directly impact sales team efficiency and conversion rates

**Dependencies**: 
- Backend Sales Service (Port 8009) ✅ Ready
- Backend Charter Service (Port 8001) ✅ Ready
- Backend Pricing Service (Port 8007) ✅ Ready

**Team Allocation**:
- **Senior Dev**: Advanced Quote Builder, Pricing Integration
- **Junior Dev**: Lead Management CRUD, Agent Dashboard

---

## Week 1: Lead Management Foundation

### Feature 1.1: Lead List View

**Estimated Time**: 2 days

#### Step-by-Step Implementation

**Task 1.1.1: Create Feature Structure** (1 hour)

```bash
mkdir -p frontend/src/features/leads/components
mkdir -p frontend/src/features/leads/hooks
mkdir -p frontend/src/features/leads/api
mkdir -p frontend/src/features/leads/types
```

**Task 1.1.2: Define TypeScript Interfaces** (1 hour)

Create `frontend/src/features/leads/types/lead.types.ts`:

```typescript
export interface Lead {
  id: number
  name: string
  company_name: string | null
  email: string
  phone: string
  source: 'website' | 'referral' | 'cold_call' | 'event' | 'other'
  status: 'new' | 'contacted' | 'qualified' | 'quote_sent' | 'converted' | 'lost'
  assigned_to: number | null
  assigned_to_name: string | null
  trip_type: string | null
  passengers: number | null
  trip_date: string | null
  notes: string | null
  created_at: string
  updated_at: string | null
  last_contact_date: string | null
}

export interface CreateLeadRequest {
  name: string
  company_name?: string
  email: string
  phone: string
  source: string
  trip_type?: string
  passengers?: number
  trip_date?: string
  notes?: string
}

export interface UpdateLeadRequest {
  name?: string
  company_name?: string
  email?: string
  phone?: string
  status?: string
  assigned_to?: number
  trip_type?: string
  passengers?: number
  trip_date?: string
  notes?: string
}

export interface LeadFilters {
  status?: string
  source?: string
  assigned_to?: number
  search?: string
  date_from?: string
  date_to?: string
}
```

**Task 1.1.3: Create API Service** (2 hours)

Create `frontend/src/features/leads/api/leadApi.ts`:

```typescript
import api from '@/services/api'
import { Lead, CreateLeadRequest, UpdateLeadRequest, LeadFilters } from '../types/lead.types'

export const leadApi = {
  getAll: async (filters?: LeadFilters) => {
    const params = new URLSearchParams()
    if (filters?.status) params.append('status', filters.status)
    if (filters?.source) params.append('source', filters.source)
    if (filters?.assigned_to) params.append('assigned_to', filters.assigned_to.toString())
    if (filters?.search) params.append('search', filters.search)
    if (filters?.date_from) params.append('date_from', filters.date_from)
    if (filters?.date_to) params.append('date_to', filters.date_to)
    
    const response = await api.get<Lead[]>(`/api/v1/sales/leads?${params}`)
    return response.data
  },
  
  getById: async (id: number) => {
    const response = await api.get<Lead>(`/api/v1/sales/leads/${id}`)
    return response.data
  },
  
  create: async (data: CreateLeadRequest) => {
    const response = await api.post<Lead>('/api/v1/sales/leads', data)
    return response.data
  },
  
  update: async (id: number, data: UpdateLeadRequest) => {
    const response = await api.patch<Lead>(`/api/v1/sales/leads/${id}`, data)
    return response.data
  },
  
  delete: async (id: number) => {
    await api.delete(`/api/v1/sales/leads/${id}`)
  },
  
  convertToQuote: async (id: number) => {
    const response = await api.post<{ charter_id: number }>(`/api/v1/sales/leads/${id}/convert`)
    return response.data
  },
  
  assign: async (id: number, userId: number) => {
    const response = await api.post(`/api/v1/sales/leads/${id}/assign`, { user_id: userId })
    return response.data
  }
}
```

**Task 1.1.4: Create Custom Hooks** (2 hours)

Create `frontend/src/features/leads/hooks/useLeadQuery.ts`:

```typescript
import { useQuery } from '@tanstack/react-query'
import { leadApi } from '../api/leadApi'
import { LeadFilters } from '../types/lead.types'

export function useLeads(filters?: LeadFilters) {
  return useQuery({
    queryKey: ['leads', filters],
    queryFn: () => leadApi.getAll(filters),
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

export function useLead(id: number) {
  return useQuery({
    queryKey: ['leads', id],
    queryFn: () => leadApi.getById(id),
    enabled: !!id,
  })
}
```

Create `frontend/src/features/leads/hooks/useLeadMutation.ts`:

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { leadApi } from '../api/leadApi'
import { CreateLeadRequest, UpdateLeadRequest } from '../types/lead.types'

export function useCreateLead() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  
  return useMutation({
    mutationFn: leadApi.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['leads'] })
      toast.success('Lead created successfully')
      navigate(`/leads/${data.id}`)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create lead')
    }
  })
}

export function useUpdateLead(id: number) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: UpdateLeadRequest) => leadApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads', id] })
      queryClient.invalidateQueries({ queryKey: ['leads'] })
      toast.success('Lead updated successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update lead')
    }
  })
}

export function useDeleteLead() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  
  return useMutation({
    mutationFn: leadApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] })
      toast.success('Lead deleted successfully')
      navigate('/leads')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete lead')
    }
  })
}

export function useConvertLeadToQuote(id: number) {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  
  return useMutation({
    mutationFn: () => leadApi.convertToQuote(id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['leads'] })
      toast.success('Lead converted to quote successfully')
      navigate(`/charters/${data.charter_id}`)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to convert lead')
    }
  })
}

export function useAssignLead(id: number) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (userId: number) => leadApi.assign(id, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads', id] })
      queryClient.invalidateQueries({ queryKey: ['leads'] })
      toast.success('Lead assigned successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to assign lead')
    }
  })
}
```

**Task 1.1.5: Build Lead List Component** (4 hours)

Create `frontend/src/features/leads/components/LeadList.tsx`:

```typescript
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Chip,
  CircularProgress,
  Alert,
  TextField,
  Grid,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Typography,
  InputAdornment
} from '@mui/material'
import {
  Search as SearchIcon,
  Add as AddIcon,
  PersonAdd as AssignIcon
} from '@mui/icons-material'
import { useLeads } from '../hooks/useLeadQuery'
import { LeadFilters } from '../types/lead.types'
import { format } from 'date-fns'

export default function LeadList() {
  const navigate = useNavigate()
  const [filters, setFilters] = useState<LeadFilters>({})
  
  const { data: leads, isLoading, error } = useLeads(filters)
  
  const handleFilterChange = (key: keyof LeadFilters, value: string) => {
    setFilters(prev => ({
      ...prev,
      [key]: value || undefined
    }))
  }
  
  const getStatusColor = (status: string) => {
    const colors: Record<string, 'default' | 'primary' | 'success' | 'warning' | 'error' | 'info'> = {
      new: 'info',
      contacted: 'primary',
      qualified: 'success',
      quote_sent: 'warning',
      converted: 'success',
      lost: 'error'
    }
    return colors[status] || 'default'
  }
  
  const formatDate = (dateString: string) => {
    return format(new Date(dateString), 'MMM dd, yyyy')
  }
  
  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }
  
  if (error) {
    return (
      <Alert severity="error">
        Failed to load leads. Please try again.
      </Alert>
    )
  }
  
  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Leads</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/leads/new')}
        >
          Add Lead
        </Button>
      </Box>
      
      {/* Filters */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              size="small"
              label="Search"
              placeholder="Name, email, or company"
              value={filters.search || ''}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                )
              }}
            />
          </Grid>
          
          <Grid item xs={12} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select
                value={filters.status || ''}
                label="Status"
                onChange={(e) => handleFilterChange('status', e.target.value)}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="new">New</MenuItem>
                <MenuItem value="contacted">Contacted</MenuItem>
                <MenuItem value="qualified">Qualified</MenuItem>
                <MenuItem value="quote_sent">Quote Sent</MenuItem>
                <MenuItem value="converted">Converted</MenuItem>
                <MenuItem value="lost">Lost</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Source</InputLabel>
              <Select
                value={filters.source || ''}
                label="Source"
                onChange={(e) => handleFilterChange('source', e.target.value)}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="website">Website</MenuItem>
                <MenuItem value="referral">Referral</MenuItem>
                <MenuItem value="cold_call">Cold Call</MenuItem>
                <MenuItem value="event">Event</MenuItem>
                <MenuItem value="other">Other</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} md={2}>
            <TextField
              fullWidth
              size="small"
              type="date"
              label="From Date"
              value={filters.date_from || ''}
              onChange={(e) => handleFilterChange('date_from', e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          
          <Grid item xs={12} md={2}>
            <TextField
              fullWidth
              size="small"
              type="date"
              label="To Date"
              value={filters.date_to || ''}
              onChange={(e) => handleFilterChange('date_to', e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
        </Grid>
      </Paper>
      
      {/* Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Company</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Phone</TableCell>
              <TableCell>Source</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Assigned To</TableCell>
              <TableCell>Created</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {leads && leads.length === 0 ? (
              <TableRow>
                <TableCell colSpan={10} align="center">
                  <Typography color="textSecondary" sx={{ py: 3 }}>
                    No leads found. Create your first lead!
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              leads?.map((lead) => (
                <TableRow
                  key={lead.id}
                  hover
                  sx={{ cursor: 'pointer' }}
                  onDoubleClick={() => navigate(`/leads/${lead.id}`)}
                >
                  <TableCell>{lead.id}</TableCell>
                  <TableCell>{lead.name}</TableCell>
                  <TableCell>{lead.company_name || '-'}</TableCell>
                  <TableCell>{lead.email}</TableCell>
                  <TableCell>{lead.phone}</TableCell>
                  <TableCell>
                    <Chip label={lead.source} size="small" />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={lead.status}
                      color={getStatusColor(lead.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{lead.assigned_to_name || 'Unassigned'}</TableCell>
                  <TableCell>{formatDate(lead.created_at)}</TableCell>
                  <TableCell align="center">
                    <Button
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation()
                        navigate(`/leads/${lead.id}`)
                      }}
                    >
                      View
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}
```

**Task 1.1.6: Add Route and Navigation** (30 minutes)

Update `frontend/src/App.tsx`:

```typescript
// Add import
import LeadList from './features/leads/components/LeadList'

// Add route (inside NonVendorRoute protected routes)
<Route
  path="/leads"
  element={
    <ProtectedRoute>
      <Layout>
        <NonVendorRoute>
          <LeadList />
        </NonVendorRoute>
      </Layout>
    </ProtectedRoute>
  }
/>
```

Update `frontend/src/components/Layout.tsx`:

```typescript
// Add to menuItems array
{ 
  text: 'Leads', 
  icon: <PersonAddIcon />, 
  path: '/leads', 
  showForVendor: false 
},
```

**Testing Checklist** (1 hour):
- [ ] Lead list loads without errors
- [ ] Filters work correctly (status, source, search, date range)
- [ ] Table displays all lead fields
- [ ] Status chips show correct colors
- [ ] Double-click navigates to lead detail
- [ ] "Add Lead" button navigates to create form
- [ ] Empty state shows when no leads
- [ ] Loading spinner shows while fetching
- [ ] Error message shows on API failure

---

### Feature 1.2: Lead Create/Edit Form

**Estimated Time**: 2 days

#### Step-by-Step Implementation

**Task 1.2.1: Create Lead Form Component** (4 hours)

Create `frontend/src/features/leads/components/LeadForm.tsx`:

```typescript
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Box,
  Paper,
  TextField,
  Button,
  Grid,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert
} from '@mui/material'
import { Save as SaveIcon, Cancel as CancelIcon } from '@mui/icons-material'
import { useCreateLead, useUpdateLead } from '../hooks/useLeadMutation'
import { Lead } from '../types/lead.types'

const leadSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  company_name: z.string().optional(),
  email: z.string().email('Invalid email address'),
  phone: z.string().min(10, 'Phone must be at least 10 digits'),
  source: z.enum(['website', 'referral', 'cold_call', 'event', 'other']),
  trip_type: z.string().optional(),
  passengers: z.number().int().positive().optional().nullable(),
  trip_date: z.string().optional(),
  notes: z.string().optional(),
})

type LeadFormData = z.infer<typeof leadSchema>

interface LeadFormProps {
  lead?: Lead
  mode: 'create' | 'edit'
}

export default function LeadForm({ lead, mode }: LeadFormProps) {
  const navigate = useNavigate()
  const createMutation = useCreateLead()
  const updateMutation = useUpdateLead(lead?.id || 0)
  
  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
    reset
  } = useForm<LeadFormData>({
    resolver: zodResolver(leadSchema),
    defaultValues: lead ? {
      name: lead.name,
      company_name: lead.company_name || '',
      email: lead.email,
      phone: lead.phone,
      source: lead.source,
      trip_type: lead.trip_type || '',
      passengers: lead.passengers || undefined,
      trip_date: lead.trip_date || '',
      notes: lead.notes || '',
    } : {
      source: 'website',
      passengers: undefined,
    }
  })
  
  useEffect(() => {
    if (lead) {
      reset({
        name: lead.name,
        company_name: lead.company_name || '',
        email: lead.email,
        phone: lead.phone,
        source: lead.source,
        trip_type: lead.trip_type || '',
        passengers: lead.passengers || undefined,
        trip_date: lead.trip_date || '',
        notes: lead.notes || '',
      })
    }
  }, [lead, reset])
  
  const onSubmit = (data: LeadFormData) => {
    if (mode === 'create') {
      createMutation.mutate(data)
    } else {
      updateMutation.mutate(data)
    }
  }
  
  const mutation = mode === 'create' ? createMutation : updateMutation
  
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          {mode === 'create' ? 'Create Lead' : 'Edit Lead'}
        </Typography>
      </Box>
      
      <Paper sx={{ p: 3 }}>
        <Box component="form" onSubmit={handleSubmit(onSubmit)}>
          <Grid container spacing={3}>
            {/* Contact Information */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Contact Information
              </Typography>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                {...register('name')}
                label="Name"
                fullWidth
                required
                error={!!errors.name}
                helperText={errors.name?.message}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                {...register('company_name')}
                label="Company Name"
                fullWidth
                error={!!errors.company_name}
                helperText={errors.company_name?.message}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                {...register('email')}
                label="Email"
                type="email"
                fullWidth
                required
                error={!!errors.email}
                helperText={errors.email?.message}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                {...register('phone')}
                label="Phone"
                fullWidth
                required
                error={!!errors.phone}
                helperText={errors.phone?.message}
                placeholder="(555) 123-4567"
              />
            </Grid>
            
            {/* Lead Details */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                Lead Details
              </Typography>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControl fullWidth required error={!!errors.source}>
                <InputLabel>Source</InputLabel>
                <Controller
                  name="source"
                  control={control}
                  render={({ field }) => (
                    <Select {...field} label="Source">
                      <MenuItem value="website">Website</MenuItem>
                      <MenuItem value="referral">Referral</MenuItem>
                      <MenuItem value="cold_call">Cold Call</MenuItem>
                      <MenuItem value="event">Event</MenuItem>
                      <MenuItem value="other">Other</MenuItem>
                    </Select>
                  )}
                />
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                {...register('trip_type')}
                label="Trip Type"
                fullWidth
                error={!!errors.trip_type}
                helperText={errors.trip_type?.message}
                placeholder="e.g., Corporate Event, Wedding, School Trip"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                {...register('passengers', { valueAsNumber: true })}
                label="Estimated Passengers"
                type="number"
                fullWidth
                error={!!errors.passengers}
                helperText={errors.passengers?.message}
                InputProps={{ inputProps: { min: 1 } }}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                {...register('trip_date')}
                label="Estimated Trip Date"
                type="date"
                fullWidth
                error={!!errors.trip_date}
                helperText={errors.trip_date?.message}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                {...register('notes')}
                label="Notes"
                fullWidth
                multiline
                rows={4}
                error={!!errors.notes}
                helperText={errors.notes?.message}
                placeholder="Additional information about this lead..."
              />
            </Grid>
            
            {/* Error Message */}
            {mutation.isError && (
              <Grid item xs={12}>
                <Alert severity="error">
                  {mutation.error?.message || `Failed to ${mode} lead`}
                </Alert>
              </Grid>
            )}
            
            {/* Actions */}
            <Grid item xs={12}>
              <Box display="flex" gap={2} justifyContent="flex-end">
                <Button
                  variant="outlined"
                  startIcon={<CancelIcon />}
                  onClick={() => navigate('/leads')}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  startIcon={<SaveIcon />}
                  disabled={mutation.isPending}
                >
                  {mutation.isPending ? 'Saving...' : 'Save Lead'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </Box>
      </Paper>
    </Box>
  )
}
```

**Task 1.2.2: Create Lead Create Page** (30 minutes)

Create `frontend/src/features/leads/components/LeadCreate.tsx`:

```typescript
import LeadForm from './LeadForm'

export default function LeadCreate() {
  return <LeadForm mode="create" />
}
```

**Task 1.2.3: Add Routes** (15 minutes)

Update `frontend/src/App.tsx`:

```typescript
import LeadCreate from './features/leads/components/LeadCreate'

// Add route
<Route
  path="/leads/new"
  element={
    <ProtectedRoute>
      <Layout>
        <NonVendorRoute>
          <LeadCreate />
        </NonVendorRoute>
      </Layout>
    </ProtectedRoute>
  }
/>
```

**Testing Checklist** (1 hour):
- [ ] Form loads with empty fields (create mode)
- [ ] All fields validate correctly
- [ ] Required fields show errors when empty
- [ ] Email validation works
- [ ] Phone validation works (minimum 10 digits)
- [ ] Source dropdown has all options
- [ ] Passenger count only accepts positive integers
- [ ] Date picker works
- [ ] Form submits successfully
- [ ] Redirects to lead detail after creation
- [ ] Toast notification shows on success
- [ ] Error message shows on failure
- [ ] Cancel button returns to lead list

---

**Continue to [Week 2: Lead Detail and Pipeline](phase_1.md#week-2)**

---

## Week 2: Lead Detail and Pipeline Management

(Content continues with similar detailed structure...)

---

## Week 3: Advanced Quote Builder

(Content continues...)

---

## Week 4: Agent Dashboard and Charter Cloning

(Content continues...)

---

## Deliverables Checklist

- [ ] Lead management (CRUD operations)
- [ ] Lead list with filters
- [ ] Lead detail view
- [ ] Lead assignment workflow
- [ ] Convert lead to quote
- [ ] Advanced quote builder with pricing
- [ ] DOT compliance calculations
- [ ] Amenity selection
- [ ] Promo code validation
- [ ] Agent dashboard
- [ ] Charter cloning (single and multi-date)
- [ ] Recurring charter UI
- [ ] All routes added to App.tsx
- [ ] All menu items added to Layout.tsx
- [ ] All API integrations tested
- [ ] All forms validated
- [ ] All error handling implemented
- [ ] Code reviewed and approved
- [ ] Documentation updated

---

[← Back to Implementation Plan](README.md) | [Next Phase: Change Management →](phase_2.md)
