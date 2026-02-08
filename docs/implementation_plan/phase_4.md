# Phase 4: Dispatch & Operations
## Duration: 3 weeks | Priority: Medium

[← Back to Implementation Plan](README.md) | [← Phase 3](phase_3.md)

---

## Overview

**Goal**: Build visual dispatch board, GPS tracking integration, route optimization, and recovery management.

**Business Impact**: Medium-High - Improves operational efficiency and driver management.

**Dependencies**:
- Backend Dispatch Service (Port 8004) ✅ Ready
- Backend Charter Service (Port 8001) ✅ Ready
- Backend Vendor Service (Port 8002) ✅ Ready

**Team Allocation**:
- **Senior Dev**: GPS integration, route optimization
- **Junior Dev**: Dispatch board UI, driver assignment

---

## Week 1: Dispatch Board Foundation

### Feature 4.1: Visual Dispatch Board

**Estimated Time**: 3 days

#### Step-by-Step Implementation

**Task 4.1.1: Create Dispatch Feature Structure** (30 minutes)

```bash
mkdir -p frontend/src/features/dispatch/components
mkdir -p frontend/src/features/dispatch/hooks
mkdir -p frontend/src/features/dispatch/api
mkdir -p frontend/src/features/dispatch/types
```

**Task 4.1.2: Define Types** (1 hour)

Create `frontend/src/features/dispatch/types/dispatch.types.ts`:

```typescript
export interface DispatchTrip {
  id: number
  reference_number: string
  client_name: string
  pickup_date: string
  pickup_time: string
  pickup_location: string
  dropoff_location: string
  passengers: number
  vehicle_type: string
  vendor_id: number | null
  vendor_name: string | null
  driver_id: number | null
  driver_name: string | null
  status: 'unassigned' | 'assigned' | 'in_transit' | 'completed' | 'cancelled'
  priority: 'low' | 'normal' | 'high' | 'urgent'
  notes: string | null
}

export interface DispatchDriver {
  id: number
  name: string
  phone: string
  vendor_id: number
  vendor_name: string
  current_location: {
    latitude: number
    longitude: number
  } | null
  status: 'available' | 'assigned' | 'in_transit' | 'off_duty'
  assigned_trips_today: number
}

export interface DispatchFilters {
  date?: string
  status?: string
  vendor_id?: number
  priority?: string
}
```

**Task 4.1.3: Create API Service** (2 hours)

Create `frontend/src/features/dispatch/api/dispatchApi.ts`:

```typescript
import api from '@/services/api'
import { DispatchTrip, DispatchDriver, DispatchFilters } from '../types/dispatch.types'

export const dispatchApi = {
  getTrips: async (filters?: DispatchFilters) => {
    const params = new URLSearchParams()
    if (filters?.date) params.append('date', filters.date)
    if (filters?.status) params.append('status', filters.status)
    if (filters?.vendor_id) params.append('vendor_id', filters.vendor_id.toString())
    if (filters?.priority) params.append('priority', filters.priority)
    
    const response = await api.get<DispatchTrip[]>(`/api/v1/dispatch/trips?${params}`)
    return response.data
  },
  
  getDrivers: async () => {
    const response = await api.get<DispatchDriver[]>('/api/v1/dispatch/drivers')
    return response.data
  },
  
  assignDriver: async (tripId: number, driverId: number) => {
    const response = await api.post(`/api/v1/dispatch/trips/${tripId}/assign`, {
      driver_id: driverId
    })
    return response.data
  },
  
  unassignDriver: async (tripId: number) => {
    const response = await api.post(`/api/v1/dispatch/trips/${tripId}/unassign`)
    return response.data
  },
  
  updateTripStatus: async (tripId: number, status: string) => {
    const response = await api.patch(`/api/v1/dispatch/trips/${tripId}/status`, { status })
    return response.data
  },
  
  updatePriority: async (tripId: number, priority: string) => {
    const response = await api.patch(`/api/v1/dispatch/trips/${tripId}/priority`, { priority })
    return response.data
  }
}
```

**Task 4.1.4: Create Dispatch Board Component** (6 hours)

Create `frontend/src/features/dispatch/components/DispatchBoard.tsx`:

```typescript
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Paper,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material'
import {
  Person as DriverIcon,
  LocationOn as LocationIcon,
  Schedule as TimeIcon,
  Flag as FlagIcon,
  Refresh as RefreshIcon,
  DragIndicator as DragIcon
} from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd'
import toast from 'react-hot-toast'
import { dispatchApi } from '../api/dispatchApi'
import { DispatchTrip, DispatchDriver, DispatchFilters } from '../types/dispatch.types'
import { format } from 'date-fns'

export default function DispatchBoard() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [filters, setFilters] = useState<DispatchFilters>({
    date: format(new Date(), 'yyyy-MM-dd')
  })
  const [assignDialog, setAssignDialog] = useState<{
    open: boolean
    trip?: DispatchTrip
  }>({ open: false })
  
  const { data: trips, isLoading, refetch } = useQuery({
    queryKey: ['dispatch-trips', filters],
    queryFn: () => dispatchApi.getTrips(filters),
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  })
  
  const { data: drivers } = useQuery({
    queryKey: ['dispatch-drivers'],
    queryFn: dispatchApi.getDrivers,
    refetchInterval: 30000,
  })
  
  const assignMutation = useMutation({
    mutationFn: ({ tripId, driverId }: { tripId: number; driverId: number }) =>
      dispatchApi.assignDriver(tripId, driverId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dispatch-trips'] })
      queryClient.invalidateQueries({ queryKey: ['dispatch-drivers'] })
      toast.success('Driver assigned successfully')
      setAssignDialog({ open: false })
    },
    onError: () => {
      toast.error('Failed to assign driver')
    }
  })
  
  const updateStatusMutation = useMutation({
    mutationFn: ({ tripId, status }: { tripId: number; status: string }) =>
      dispatchApi.updateTripStatus(tripId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dispatch-trips'] })
      toast.success('Status updated')
    }
  })
  
  // Group trips by status
  const groupedTrips = {
    unassigned: trips?.filter(t => t.status === 'unassigned') || [],
    assigned: trips?.filter(t => t.status === 'assigned') || [],
    in_transit: trips?.filter(t => t.status === 'in_transit') || [],
    completed: trips?.filter(t => t.status === 'completed') || []
  }
  
  const getPriorityColor = (priority: string) => {
    const colors: Record<string, 'default' | 'primary' | 'warning' | 'error'> = {
      low: 'default',
      normal: 'primary',
      high: 'warning',
      urgent: 'error'
    }
    return colors[priority] || 'default'
  }
  
  const handleDragEnd = (result: any) => {
    if (!result.destination) return
    
    const { draggableId, destination } = result
    const tripId = parseInt(draggableId.split('-')[1])
    const newStatus = destination.droppableId
    
    updateStatusMutation.mutate({ tripId, newStatus })
  }
  
  const handleAssignClick = (trip: DispatchTrip) => {
    setAssignDialog({ open: true, trip })
  }
  
  const handleDriverSelect = (driverId: number) => {
    if (assignDialog.trip) {
      assignMutation.mutate({
        tripId: assignDialog.trip.id,
        driverId
      })
    }
  }
  
  const TripCard = ({ trip, index }: { trip: DispatchTrip; index: number }) => (
    <Draggable draggableId={`trip-${trip.id}`} index={index}>
      {(provided) => (
        <Card
          ref={provided.innerRef}
          {...provided.draggableProps}
          {...provided.dragHandleProps}
          sx={{
            mb: 1,
            cursor: 'pointer',
            '&:hover': { boxShadow: 3 }
          }}
        >
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="flex-start">
              <Box>
                <Typography variant="body2" fontWeight="bold">
                  {trip.reference_number}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  {trip.client_name}
                </Typography>
              </Box>
              <Box>
                <Chip
                  icon={<FlagIcon />}
                  label={trip.priority}
                  color={getPriorityColor(trip.priority)}
                  size="small"
                />
              </Box>
            </Box>
            
            <Box mt={1} display="flex" alignItems="center" gap={1}>
              <TimeIcon fontSize="small" color="action" />
              <Typography variant="caption">
                {trip.pickup_time}
              </Typography>
            </Box>
            
            <Box display="flex" alignItems="center" gap={1}>
              <LocationIcon fontSize="small" color="action" />
              <Typography variant="caption" noWrap>
                {trip.pickup_location}
              </Typography>
            </Box>
            
            {trip.driver_name && (
              <Box display="flex" alignItems="center" gap={1} mt={1}>
                <DriverIcon fontSize="small" color="primary" />
                <Typography variant="caption">
                  {trip.driver_name}
                </Typography>
              </Box>
            )}
            
            <Box mt={1} display="flex" gap={1}>
              <Button
                size="small"
                variant="outlined"
                onClick={(e) => {
                  e.stopPropagation()
                  navigate(`/charters/${trip.id}`)
                }}
              >
                View
              </Button>
              {trip.status === 'unassigned' && (
                <Button
                  size="small"
                  variant="contained"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleAssignClick(trip)
                  }}
                >
                  Assign
                </Button>
              )}
            </Box>
          </CardContent>
        </Card>
      )}
    </Draggable>
  )
  
  const Column = ({ title, status, trips }: { title: string; status: string; trips: DispatchTrip[] }) => (
    <Paper sx={{ p: 2, height: 'calc(100vh - 250px)', overflow: 'auto' }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">{title}</Typography>
        <Chip label={trips.length} size="small" />
      </Box>
      <Droppable droppableId={status}>
        {(provided) => (
          <Box ref={provided.innerRef} {...provided.droppableProps}>
            {trips.map((trip, index) => (
              <TripCard key={trip.id} trip={trip} index={index} />
            ))}
            {provided.placeholder}
          </Box>
        )}
      </Droppable>
    </Paper>
  )
  
  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Dispatch Board</Typography>
        <Box display="flex" gap={2}>
          <IconButton onClick={() => refetch()}>
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>
      
      {/* Filters */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              size="small"
              type="date"
              label="Date"
              value={filters.date}
              onChange={(e) => setFilters({ ...filters, date: e.target.value })}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          
          <Grid item xs={12} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Priority</InputLabel>
              <Select
                value={filters.priority || ''}
                label="Priority"
                onChange={(e) => setFilters({ ...filters, priority: e.target.value || undefined })}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="urgent">Urgent</MenuItem>
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="normal">Normal</MenuItem>
                <MenuItem value="low">Low</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>
      
      {/* Dispatch Board */}
      <DragDropContext onDragEnd={handleDragEnd}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={3}>
            <Column title="Unassigned" status="unassigned" trips={groupedTrips.unassigned} />
          </Grid>
          <Grid item xs={12} md={3}>
            <Column title="Assigned" status="assigned" trips={groupedTrips.assigned} />
          </Grid>
          <Grid item xs={12} md={3}>
            <Column title="In Transit" status="in_transit" trips={groupedTrips.in_transit} />
          </Grid>
          <Grid item xs={12} md={3}>
            <Column title="Completed" status="completed" trips={groupedTrips.completed} />
          </Grid>
        </Grid>
      </DragDropContext>
      
      {/* Assign Driver Dialog */}
      <Dialog
        open={assignDialog.open}
        onClose={() => setAssignDialog({ open: false })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Assign Driver</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary" gutterBottom>
            Trip: {assignDialog.trip?.reference_number}
          </Typography>
          
          <List>
            {drivers
              ?.filter(d => d.status === 'available' || d.status === 'assigned')
              .map((driver) => (
                <ListItem key={driver.id} disablePadding>
                  <ListItemButton onClick={() => handleDriverSelect(driver.id)}>
                    <ListItemText
                      primary={driver.name}
                      secondary={
                        <>
                          {driver.vendor_name} • {driver.phone}
                          <br />
                          Trips today: {driver.assigned_trips_today}
                        </>
                      }
                    />
                    <Chip
                      label={driver.status}
                      color={driver.status === 'available' ? 'success' : 'default'}
                      size="small"
                    />
                  </ListItemButton>
                </ListItem>
              ))}
          </List>
        </DialogContent>
      </Dialog>
    </Box>
  )
}
```

**Task 4.1.5: Install Dependencies** (15 minutes)

```bash
cd frontend
npm install react-beautiful-dnd @types/react-beautiful-dnd
```

**Task 4.1.6: Add Route** (15 minutes)

Update `frontend/src/App.tsx`:

```typescript
import DispatchBoard from './features/dispatch/components/DispatchBoard'

<Route
  path="/dispatch"
  element={
    <ProtectedRoute>
      <Layout>
        <NonVendorRoute>
          <DispatchBoard />
        </NonVendorRoute>
      </Layout>
    </ProtectedRoute>
  }
/>
```

Update `frontend/src/components/Layout.tsx`:

```typescript
{ 
  text: 'Dispatch', 
  icon: <LocalShippingIcon />, 
  path: '/dispatch', 
  showForVendor: false 
},
```

**Testing Checklist**:
- [ ] Dispatch board loads
- [ ] Trips grouped by status
- [ ] Drag and drop works
- [ ] Status updates on drop
- [ ] Assign driver dialog opens
- [ ] Driver assignment works
- [ ] Priority badges colored correctly
- [ ] Auto-refresh works (30s)
- [ ] Filters work
- [ ] View button navigates

---

## Week 2: GPS Tracking & Route Optimization

### Feature 4.2: GPS Map View

**Estimated Time**: 3 days

#### Implementation Tasks

**Task 4.2.1: Map Component** (4 hours)

Create `frontend/src/features/dispatch/components/GPSMapView.tsx`:

```typescript
import { useEffect, useRef, useState } from 'react'
import { Box, Paper, Typography, Chip, Card, CardContent } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import api from '@/services/api'

interface DriverLocation {
  driver_id: number
  driver_name: string
  latitude: number
  longitude: number
  speed: number
  heading: number
  updated_at: string
}

export default function GPSMapView() {
  const mapRef = useRef<HTMLDivElement>(null)
  
  const { data: locations } = useQuery({
    queryKey: ['driver-locations'],
    queryFn: async () => {
      const response = await api.get<DriverLocation[]>('/api/v1/dispatch/drivers/locations')
      return response.data
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  })
  
  useEffect(() => {
    // Initialize map (Leaflet, Google Maps, or Mapbox)
    // This is a placeholder - actual implementation would use a map library
    if (mapRef.current && locations) {
      console.log('Map would render', locations.length, 'driver locations')
    }
  }, [locations])
  
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Live GPS Tracking
      </Typography>
      
      <Box display="flex" gap={2}>
        {/* Map */}
        <Paper sx={{ flex: 1, height: '600px', p: 2 }}>
          <div ref={mapRef} style={{ width: '100%', height: '100%' }}>
            <Typography color="textSecondary">
              Map will be integrated here (Leaflet/Google Maps/Mapbox)
            </Typography>
          </div>
        </Paper>
        
        {/* Driver List */}
        <Box sx={{ width: 300 }}>
          <Typography variant="h6" gutterBottom>
            Active Drivers
          </Typography>
          {locations?.map((location) => (
            <Card key={location.driver_id} sx={{ mb: 1 }}>
              <CardContent>
                <Typography variant="body1" fontWeight="bold">
                  {location.driver_name}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Speed: {location.speed} mph
                </Typography>
                <br />
                <Typography variant="caption" color="textSecondary">
                  Updated: {new Date(location.updated_at).toLocaleTimeString()}
                </Typography>
              </CardContent>
            </Card>
          ))}
        </Box>
      </Box>
    </Box>
  )
}
```

**Testing Checklist**:
- [ ] Map component renders
- [ ] Driver locations display
- [ ] Auto-refresh works
- [ ] Speed/heading shown
- [ ] Last update timestamp shown

---

## Week 3: Recovery Management

### Feature 4.3: Recovery Workflow

**Estimated Time**: 2 days

#### Implementation Tasks

**Task 4.3.1: Recovery Dashboard** (3 hours)

Create `frontend/src/features/dispatch/components/RecoveryDashboard.tsx`:

```typescript
import { useState } from 'react'
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Typography,
  Chip
} from '@mui/material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import api from '@/services/api'

interface RecoveryCase {
  id: number
  charter_id: number
  reference_number: string
  reason: string
  status: 'open' | 'vendor_sourced' | 'resolved'
  created_at: string
}

export default function RecoveryDashboard() {
  const queryClient = useQueryClient()
  const [recoveryDialog, setRecoveryDialog] = useState({
    open: false,
    charterId: 0
  })
  const [reason, setReason] = useState('')
  
  const { data: cases } = useQuery({
    queryKey: ['recovery-cases'],
    queryFn: async () => {
      const response = await api.get<RecoveryCase[]>('/api/v1/dispatch/recovery')
      return response.data
    }
  })
  
  const createRecoveryMutation = useMutation({
    mutationFn: async () => {
      return api.post('/api/v1/dispatch/recovery', {
        charter_id: recoveryDialog.charterId,
        reason
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recovery-cases'] })
      toast.success('Recovery case created')
      setRecoveryDialog({ open: false, charterId: 0 })
      setReason('')
    },
    onError: () => {
      toast.error('Failed to create recovery case')
    }
  })
  
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Recovery Management</Typography>
      </Box>
      
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Charter</TableCell>
              <TableCell>Reason</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {cases?.map((c) => (
              <TableRow key={c.id}>
                <TableCell>{c.id}</TableCell>
                <TableCell>{c.reference_number}</TableCell>
                <TableCell>{c.reason}</TableCell>
                <TableCell>
                  <Chip
                    label={c.status}
                    color={c.status === 'resolved' ? 'success' : 'warning'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {new Date(c.created_at).toLocaleString()}
                </TableCell>
                <TableCell align="center">
                  <Button size="small">Resolve</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      
      {/* Recovery Dialog */}
      <Dialog
        open={recoveryDialog.open}
        onClose={() => setRecoveryDialog({ open: false, charterId: 0 })}
      >
        <DialogTitle>Create Recovery Case</DialogTitle>
        <DialogContent>
          <TextField
            label="Reason"
            multiline
            rows={4}
            fullWidth
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRecoveryDialog({ open: false, charterId: 0 })}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={() => createRecoveryMutation.mutate()}
            disabled={!reason}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
```

**Testing Checklist**:
- [ ] Recovery cases display
- [ ] Create case dialog works
- [ ] Case creation succeeds
- [ ] Status chips correct
- [ ] Resolve button works

---

## Deliverables Checklist

- [ ] Dispatch board with drag-drop
- [ ] Trip status columns (4)
- [ ] Driver assignment workflow
- [ ] Priority flagging
- [ ] Auto-refresh (30s interval)
- [ ] GPS map view
- [ ] Driver location tracking
- [ ] Route visualization
- [ ] Recovery case management
- [ ] Emergency vendor sourcing
- [ ] All routes configured
- [ ] All navigation updated
- [ ] Real-time updates working

---

[← Back to Implementation Plan](README.md) | [← Phase 3](phase_3.md) | [Next Phase: Accounting & Reporting →](phase_5.md)
