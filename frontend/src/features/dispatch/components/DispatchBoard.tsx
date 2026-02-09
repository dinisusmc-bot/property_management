/**
 * Dispatch Board Component
 * Visual dispatch board for trip management and driver assignment
 */
import { useState } from 'react'
import {
  Box,
  Paper,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
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
  MenuItem,
  Stack
} from '@mui/material'
import {
  Person as DriverIcon,
  LocationOn as LocationIcon,
  Schedule as TimeIcon,
  Refresh as RefreshIcon,
  Assignment as TripIcon,
  FilterList as FilterIcon
} from '@mui/icons-material'
import { useDispatchTrips, useDispatchDrivers } from '../hooks/useDispatchQuery'
import { useAssignDriver, useUnassignDriver } from '../hooks/useDispatchQuery'
import { format } from 'date-fns'

export default function DispatchBoard() {
  const [filters, setFilters] = useState({
    date: format(new Date(), 'yyyy-MM-dd'),
    status: '',
    priority: '',
  })
  const [assignDialog, setAssignDialog] = useState<{
    open: boolean
    tripId?: number
  }>({ open: false })
  const [selectedDriver, setSelectedDriver] = useState<number | ''>('')

  const { data: trips, isLoading: tripsLoading, refetch } = useDispatchTrips(filters)
  const { data: drivers } = useDispatchDrivers()
  const assignMutation = useAssignDriver()
  const unassignMutation = useUnassignDriver()

  const getStatusColor = (status: string) => {
    const colors: Record<string, any> = {
      unassigned: 'default',
      assigned: 'primary',
      in_transit: 'warning',
      completed: 'success',
      cancelled: 'error'
    }
    return colors[status] || 'default'
  }

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, any> = {
      low: 'success',
      normal: 'info',
      high: 'warning',
      urgent: 'error'
    }
    return colors[priority] || 'default'
  }

  const handleAssignDriver = (tripId: number) => {
    if (!selectedDriver) return
    
    assignMutation.mutate({ tripId, driverId: Number(selectedDriver) })
    setAssignDialog({ open: false })
    setSelectedDriver('')
  }

  const handleUnassignDriver = (tripId: number) => {
    unassignMutation.mutate(tripId)
  }

  if (tripsLoading) {
    return <Box display="flex" justifyContent="center" p={4}><Typography>Loading dispatch board...</Typography></Box>
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" component="h1">
            Dispatch Board
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {trips?.length || 0} trips | {drivers?.length || 0} drivers
          </Typography>
        </Box>
        
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => refetch()}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<FilterIcon />}
          >
            Filters
          </Button>
        </Stack>
      </Box>

      {/* Filter Bar */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              label="Date"
              type="date"
              value={filters.date}
              onChange={(e) => setFilters({ ...filters, date: e.target.value })}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={filters.status}
                label="Status"
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              >
                <MenuItem value="">All Statuses</MenuItem>
                <MenuItem value="unassigned">Unassigned</MenuItem>
                <MenuItem value="assigned">Assigned</MenuItem>
                <MenuItem value="in_transit">In Transit</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth>
              <InputLabel>Priority</InputLabel>
              <Select
                value={filters.priority}
                label="Priority"
                onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
              >
                <MenuItem value="">All Priorities</MenuItem>
                <MenuItem value="low">Low</MenuItem>
                <MenuItem value="normal">Normal</MenuItem>
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="urgent">Urgent</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Trips Grid */}
      <Grid container spacing={2}>
        {trips?.map((trip) => (
          <Grid item xs={12} sm={6} md={4} key={trip.id}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flex: 1 }}>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                  <Chip
                    label={trip.priority}
                    color={getPriorityColor(trip.priority)}
                    size="small"
                  />
                  <Chip
                    label={trip.status}
                    color={getStatusColor(trip.status)}
                    size="small"
                  />
                </Box>

                <Typography variant="h6" gutterBottom>
                  {trip.reference_number}
                </Typography>

                <Box mt={2}>
                  <Box display="flex" alignItems="center" mb={1}>
                    <LocationIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                    <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                      {trip.pickup_location || '-'} → {trip.dropoff_location || '-'}
                    </Typography>
                  </Box>
                  
                  <Box display="flex" alignItems="center" mb={1}>
                    <TimeIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                    <Typography variant="body2">
                      {trip.pickup_date} {trip.pickup_time}
                    </Typography>
                  </Box>
                  
                  <Box display="flex" alignItems="center" mb={1}>
                    <TripIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                    <Typography variant="body2">
                      {trip.passengers} passengers | {trip.vehicle_type}
                    </Typography>
                  </Box>
                </Box>

                {trip.client_name && (
                  <Box mt={2} p={1} sx={{ bgcolor: 'background.default', borderRadius: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Client: {trip.client_name}
                    </Typography>
                  </Box>
                )}

                {trip.vendor_name && (
                  <Box mt={1}>
                    <Typography variant="body2" color="text.secondary">
                      Vendor: {trip.vendor_name}
                    </Typography>
                  </Box>
                )}
              </CardContent>

              <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
                {trip.driver_name ? (
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Box display="flex" alignItems="center">
                      <DriverIcon fontSize="small" sx={{ mr: 1, color: 'primary.main' }} />
                      <Typography variant="body2">
                        {trip.driver_name}
                      </Typography>
                    </Box>
                    <Button
                      size="small"
                      onClick={() => handleUnassignDriver(trip.id!)}
                      disabled={unassignMutation.isPending}
                    >
                      Unassign
                    </Button>
                  </Box>
                ) : (
                  <Button
                    fullWidth
                    variant="outlined"
                    size="small"
                    onClick={() => setAssignDialog({ open: true, tripId: trip.id })}
                  >
                    Assign Driver
                  </Button>
                )}
              </Box>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Assign Driver Dialog */}
      <Dialog open={assignDialog.open} onClose={() => setAssignDialog({ open: false })}>
        <DialogTitle>Assign Driver to Trip</DialogTitle>
        <DialogContent>
          <List>
            {drivers?.map((driver) => (
              <ListItem key={driver.id} disablePadding>
                <ListItemButton
                  selected={selectedDriver === driver.id}
                  onClick={() => setSelectedDriver(driver.id)}
                >
                  <ListItemText
                    primary={driver.name}
                    secondary={
                      <Box display="flex" alignItems="center" gap={1}>
                        <Typography variant="body2">
                          {driver.vendor_name}
                        </Typography>
                        <Chip
                          label={driver.status}
                          size="small"
                        />
                      </Box>
                    }
                  />
                </ListItemButton>
              </ListItem>
            ))}
          </List>

          <Box display="flex" justifyContent="flex-end" mt={2} gap={1}>
            <Button onClick={() => setAssignDialog({ open: false })}>
              Cancel
            </Button>
            <Button
              variant="contained"
              onClick={() => assignDialog.tripId && handleAssignDriver(assignDialog.tripId!)}
              disabled={!selectedDriver || assignMutation.isPending}
            >
              Assign
            </Button>
          </Box>
        </DialogContent>
      </Dialog>
    </Box>
  )
}
