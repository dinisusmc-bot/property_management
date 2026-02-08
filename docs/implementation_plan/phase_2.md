# Phase 2: Change Management & Sales Support
## Duration: 3 weeks | Priority: High

[← Back to Implementation Plan](README.md) | [← Phase 1](phase_1.md)

---

## Overview

**Goal**: Implement post-booking change management system, financial flexibility features, and QC task workflows.

**Business Impact**: High - Reduces manual work for handling charter modifications and ensures quality control.

**Dependencies**:
- Backend Changes Service (Port 8012) ✅ Ready
- Backend Charter Service (Port 8001) ✅ Ready
- Backend Accounting Service (Port 8003) ✅ Ready

**Team Allocation**:
- **Senior Dev**: Change workflow, financial adjustments
- **Junior Dev**: QC task UI, change history display

---

## Week 1: Change Case System

### Feature 2.1: Change Case List

**Estimated Time**: 2 days

#### Step-by-Step Implementation

**Task 2.1.1: Create Feature Structure** (30 minutes)

```bash
mkdir -p frontend/src/features/changes/components
mkdir -p frontend/src/features/changes/hooks
mkdir -p frontend/src/features/changes/api
mkdir -p frontend/src/features/changes/types
```

**Task 2.1.2: Define TypeScript Types** (1 hour)

Create `frontend/src/features/changes/types/change.types.ts`:

```typescript
export interface ChangeCase {
  id: number
  charter_id: number
  change_type: 'itinerary' | 'vehicle' | 'passengers' | 'billing' | 'other'
  status: 'pending' | 'vendor_review' | 'client_review' | 'approved' | 'rejected' | 'completed'
  description: string
  requested_by: number
  requested_by_name: string
  created_at: string
  updated_at: string | null
  vendor_cost_change: number | null
  client_price_change: number | null
  vendor_approved_at: string | null
  client_approved_at: string | null
  approved_by: number | null
  approved_by_name: string | null
  rejection_reason: string | null
  charter_reference: string | null
}

export interface CreateChangeCaseRequest {
  charter_id: number
  change_type: string
  description: string
  vendor_cost_change?: number
  client_price_change?: number
}

export interface UpdateChangeCaseRequest {
  status?: string
  description?: string
  vendor_cost_change?: number
  client_price_change?: number
  rejection_reason?: string
}

export interface ChangeCaseFilters {
  charter_id?: number
  status?: string
  change_type?: string
  requested_by?: number
  date_from?: string
  date_to?: string
}
```

**Task 2.1.3: Create API Service** (2 hours)

Create `frontend/src/features/changes/api/changeApi.ts`:

```typescript
import api from '@/services/api'
import {
  ChangeCase,
  CreateChangeCaseRequest,
  UpdateChangeCaseRequest,
  ChangeCaseFilters
} from '../types/change.types'

export const changeApi = {
  getAll: async (filters?: ChangeCaseFilters) => {
    const params = new URLSearchParams()
    if (filters?.charter_id) params.append('charter_id', filters.charter_id.toString())
    if (filters?.status) params.append('status', filters.status)
    if (filters?.change_type) params.append('change_type', filters.change_type)
    if (filters?.requested_by) params.append('requested_by', filters.requested_by.toString())
    if (filters?.date_from) params.append('date_from', filters.date_from)
    if (filters?.date_to) params.append('date_to', filters.date_to)
    
    const response = await api.get<ChangeCase[]>(`/api/v1/changes/cases?${params}`)
    return response.data
  },
  
  getById: async (id: number) => {
    const response = await api.get<ChangeCase>(`/api/v1/changes/cases/${id}`)
    return response.data
  },
  
  getByCharter: async (charterId: number) => {
    const response = await api.get<ChangeCase[]>(`/api/v1/changes/cases?charter_id=${charterId}`)
    return response.data
  },
  
  create: async (data: CreateChangeCaseRequest) => {
    const response = await api.post<ChangeCase>('/api/v1/changes/cases', data)
    return response.data
  },
  
  update: async (id: number, data: UpdateChangeCaseRequest) => {
    const response = await api.patch<ChangeCase>(`/api/v1/changes/cases/${id}`, data)
    return response.data
  },
  
  approve: async (id: number, role: 'vendor' | 'client') => {
    const response = await api.post<ChangeCase>(`/api/v1/changes/cases/${id}/approve`, { role })
    return response.data
  },
  
  reject: async (id: number, reason: string) => {
    const response = await api.post<ChangeCase>(`/api/v1/changes/cases/${id}/reject`, { reason })
    return response.data
  },
  
  complete: async (id: number) => {
    const response = await api.post<ChangeCase>(`/api/v1/changes/cases/${id}/complete`)
    return response.data
  }
}
```

**Task 2.1.4: Create Custom Hooks** (2 hours)

Create `frontend/src/features/changes/hooks/useChangeQuery.ts`:

```typescript
import { useQuery } from '@tanstack/react-query'
import { changeApi } from '../api/changeApi'
import { ChangeCaseFilters } from '../types/change.types'

export function useChangeCases(filters?: ChangeCaseFilters) {
  return useQuery({
    queryKey: ['changes', filters],
    queryFn: () => changeApi.getAll(filters),
    staleTime: 2 * 60 * 1000,
  })
}

export function useChangeCase(id: number) {
  return useQuery({
    queryKey: ['changes', id],
    queryFn: () => changeApi.getById(id),
    enabled: !!id,
  })
}

export function useCharterChanges(charterId: number) {
  return useQuery({
    queryKey: ['changes', 'charter', charterId],
    queryFn: () => changeApi.getByCharter(charterId),
    enabled: !!charterId,
  })
}
```

Create `frontend/src/features/changes/hooks/useChangeMutation.ts`:

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { changeApi } from '../api/changeApi'
import { CreateChangeCaseRequest, UpdateChangeCaseRequest } from '../types/change.types'

export function useCreateChangeCase() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: changeApi.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['changes'] })
      queryClient.invalidateQueries({ queryKey: ['changes', 'charter', data.charter_id] })
      toast.success('Change case created successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create change case')
    }
  })
}

export function useUpdateChangeCase(id: number) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: UpdateChangeCaseRequest) => changeApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['changes', id] })
      queryClient.invalidateQueries({ queryKey: ['changes'] })
      toast.success('Change case updated successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update change case')
    }
  })
}

export function useApproveChangeCase(id: number) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (role: 'vendor' | 'client') => changeApi.approve(id, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['changes', id] })
      queryClient.invalidateQueries({ queryKey: ['changes'] })
      toast.success('Change case approved')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to approve change case')
    }
  })
}

export function useRejectChangeCase(id: number) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (reason: string) => changeApi.reject(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['changes', id] })
      queryClient.invalidateQueries({ queryKey: ['changes'] })
      toast.success('Change case rejected')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to reject change case')
    }
  })
}

export function useCompleteChangeCase(id: number) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: () => changeApi.complete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['changes', id] })
      queryClient.invalidateQueries({ queryKey: ['changes'] })
      toast.success('Change case completed')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to complete change case')
    }
  })
}
```

**Testing Checklist**:
- [ ] Change case list loads
- [ ] Filters work (status, type, charter)
- [ ] Create change case form works
- [ ] Approval workflow functions
- [ ] Rejection with reason works
- [ ] Toast notifications display
- [ ] Error handling works

---

## Week 2: Financial Flexibility

### Feature 2.2: Manual Payment Application

**Estimated Time**: 3 days

#### Implementation Tasks

**Task 2.2.1: Payment Override Form** (4 hours)

Create `frontend/src/features/payments/components/PaymentOverrideForm.tsx`:

```typescript
import { useForm } from 'react-hook-form'
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
import { Save as SaveIcon } from '@mui/icons-material'

const paymentOverrideSchema = z.object({
  charter_id: z.number().positive('Charter ID is required'),
  payment_type: z.enum(['check', 'wire', 'cash', 'other']),
  amount: z.number().positive('Amount must be positive'),
  payment_date: z.string().min(1, 'Payment date is required'),
  reference_number: z.string().optional(),
  notes: z.string().optional(),
})

type PaymentOverrideFormData = z.infer<typeof paymentOverrideSchema>

interface PaymentOverrideFormProps {
  charterId: number
  onSuccess: () => void
}

export default function PaymentOverrideForm({ charterId, onSuccess }: PaymentOverrideFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<PaymentOverrideFormData>({
    resolver: zodResolver(paymentOverrideSchema),
    defaultValues: {
      charter_id: charterId,
      payment_type: 'check',
    }
  })
  
  const onSubmit = async (data: PaymentOverrideFormData) => {
    // Implementation will use payment API
    console.log('Payment override:', data)
    onSuccess()
  }
  
  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Manual Payment Application
      </Typography>
      
      <Box component="form" onSubmit={handleSubmit(onSubmit)}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth required>
              <InputLabel>Payment Type</InputLabel>
              <Select
                {...register('payment_type')}
                label="Payment Type"
              >
                <MenuItem value="check">Check</MenuItem>
                <MenuItem value="wire">Wire Transfer</MenuItem>
                <MenuItem value="cash">Cash</MenuItem>
                <MenuItem value="other">Other</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              {...register('amount', { valueAsNumber: true })}
              label="Amount"
              type="number"
              fullWidth
              required
              error={!!errors.amount}
              helperText={errors.amount?.message}
              InputProps={{
                startAdornment: '$',
                inputProps: { min: 0, step: 0.01 }
              }}
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              {...register('payment_date')}
              label="Payment Date"
              type="date"
              fullWidth
              required
              error={!!errors.payment_date}
              helperText={errors.payment_date?.message}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              {...register('reference_number')}
              label="Reference Number"
              fullWidth
              error={!!errors.reference_number}
              helperText={errors.reference_number?.message}
              placeholder="Check #, Transaction ID, etc."
            />
          </Grid>
          
          <Grid item xs={12}>
            <TextField
              {...register('notes')}
              label="Notes"
              fullWidth
              multiline
              rows={3}
              error={!!errors.notes}
              helperText={errors.notes?.message}
            />
          </Grid>
          
          <Grid item xs={12}>
            <Box display="flex" gap={2} justifyContent="flex-end">
              <Button
                type="submit"
                variant="contained"
                startIcon={<SaveIcon />}
              >
                Apply Payment
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Box>
    </Paper>
  )
}
```

**Testing Checklist**:
- [ ] Form validates all required fields
- [ ] Amount accepts decimal values
- [ ] Date picker works
- [ ] Payment types all selectable
- [ ] Form submits successfully
- [ ] Success callback fires

---

## Week 3: QC Task System

### Feature 2.3: QC Task Dashboard

**Estimated Time**: 2 days

#### Implementation Tasks

**Task 2.3.1: QC Task Types** (1 hour)

Create `frontend/src/features/qc/types/qc.types.ts`:

```typescript
export interface QCTask {
  id: number
  charter_id: number
  task_type: 'coi_verification' | 'payment_verification' | 'itinerary_review' | 'document_check' | 'other'
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  assigned_to: number | null
  assigned_to_name: string | null
  due_date: string
  completed_at: string | null
  notes: string | null
  charter_reference: string | null
  created_at: string
}

export interface QCTaskFilters {
  status?: string
  task_type?: string
  assigned_to?: number
  overdue?: boolean
}
```

**Task 2.3.2: QC Task List Component** (3 hours)

Create `frontend/src/features/qc/components/QCTaskList.tsx`:

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
  Chip,
  Button,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid
} from '@mui/material'
import { CheckCircle as CompleteIcon } from '@mui/icons-material'
import { QCTaskFilters } from '../types/qc.types'
import { format, isPast } from 'date-fns'

export default function QCTaskList() {
  const navigate = useNavigate()
  const [filters, setFilters] = useState<QCTaskFilters>({})
  
  // Mock data for demonstration - replace with actual API call
  const tasks = [
    {
      id: 1,
      charter_id: 123,
      charter_reference: 'CH-123',
      task_type: 'coi_verification',
      status: 'pending',
      due_date: '2024-02-15',
      assigned_to_name: 'John Doe'
    }
  ]
  
  const getStatusColor = (status: string): any => {
    const colors = {
      pending: 'warning',
      in_progress: 'info',
      completed: 'success',
      failed: 'error'
    }
    return colors[status as keyof typeof colors] || 'default'
  }
  
  const getTaskTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      coi_verification: 'COI Verification',
      payment_verification: 'Payment Verification',
      itinerary_review: 'Itinerary Review',
      document_check: 'Document Check',
      other: 'Other'
    }
    return labels[type] || type
  }
  
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">QC Tasks</Typography>
      </Box>
      
      {/* Filters */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select
                value={filters.status || ''}
                label="Status"
                onChange={(e) => setFilters({ ...filters, status: e.target.value || undefined })}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="pending">Pending</MenuItem>
                <MenuItem value="in_progress">In Progress</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="failed">Failed</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Task Type</InputLabel>
              <Select
                value={filters.task_type || ''}
                label="Task Type"
                onChange={(e) => setFilters({ ...filters, task_type: e.target.value || undefined })}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="coi_verification">COI Verification</MenuItem>
                <MenuItem value="payment_verification">Payment Verification</MenuItem>
                <MenuItem value="itinerary_review">Itinerary Review</MenuItem>
                <MenuItem value="document_check">Document Check</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>
      
      {/* Task Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Charter</TableCell>
              <TableCell>Task Type</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Assigned To</TableCell>
              <TableCell>Due Date</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {tasks.map((task) => {
              const isOverdue = isPast(new Date(task.due_date)) && task.status !== 'completed'
              return (
                <TableRow
                  key={task.id}
                  hover
                  sx={{ 
                    cursor: 'pointer',
                    backgroundColor: isOverdue ? 'error.light' : 'inherit'
                  }}
                  onClick={() => navigate(`/qc-tasks/${task.id}`)}
                >
                  <TableCell>{task.id}</TableCell>
                  <TableCell>
                    <Button
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation()
                        navigate(`/charters/${task.charter_id}`)
                      }}
                    >
                      {task.charter_reference}
                    </Button>
                  </TableCell>
                  <TableCell>{getTaskTypeLabel(task.task_type)}</TableCell>
                  <TableCell>
                    <Chip
                      label={task.status}
                      color={getStatusColor(task.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{task.assigned_to_name || 'Unassigned'}</TableCell>
                  <TableCell>
                    {format(new Date(task.due_date), 'MMM dd, yyyy')}
                    {isOverdue && (
                      <Chip label="OVERDUE" color="error" size="small" sx={{ ml: 1 }} />
                    )}
                  </TableCell>
                  <TableCell align="center">
                    <Button
                      size="small"
                      startIcon={<CompleteIcon />}
                      disabled={task.status === 'completed'}
                    >
                      Complete
                    </Button>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}
```

**Testing Checklist**:
- [ ] QC task list displays
- [ ] Overdue tasks highlighted
- [ ] Filters work correctly
- [ ] Complete button updates status
- [ ] Charter link navigates correctly
- [ ] Task detail navigation works

---

## Deliverables Checklist

- [ ] Change case system (CRUD)
- [ ] Change approval workflow (vendor → client)
- [ ] Change history display
- [ ] Financial cost/price tracking
- [ ] Manual payment application form
- [ ] Payment schedule modification
- [ ] PO number linking
- [ ] QC task dashboard
- [ ] QC task assignment
- [ ] QC checklist completion
- [ ] Overdue task highlighting
- [ ] All routes added
- [ ] All navigation updated
- [ ] API integration tested
- [ ] Error handling complete

---

[← Back to Implementation Plan](README.md) | [← Phase 1](phase_1.md) | [Next Phase: Client & Vendor Portals →](phase_3.md)
