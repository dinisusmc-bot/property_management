import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Typography,
  Paper,
  Box,
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
  InputAdornment
} from '@mui/material'
import { Search as SearchIcon } from '@mui/icons-material'
import api from '../../services/api'

interface Client {
  id: number
  name: string
}

interface Vehicle {
  id: number
  name: string
}

interface Charter {
  id: number
  client_id: number
  vehicle_id: number
  vendor_id: number | null
  vendor_name: string | null
  vendor_email: string | null
  trip_date: string
  passengers: number
  trip_hours: number
  status: string
  total_cost: number
  stops?: any[]
  vehicle?: Vehicle | null
}

export default function CharterList() {
  const navigate = useNavigate()
  const [charters, setCharters] = useState<Charter[]>([])
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filters, setFilters] = useState({
    clientName: '',
    status: '',
    minCost: '',
    maxCost: ''
  })

  useEffect(() => {
    fetchCharters()
  }, [])

  const fetchCharters = async () => {
    try {
      setLoading(true)
      const clientsPromise = api.get('/api/v1/clients')
      let chartersRes
      try {
        chartersRes = await api.get('/api/v1/charters')
      } catch (listError: any) {
        const statusFilter = ['quote', 'confirmed', 'pending', 'completed']
        let recovered = false

        for (const status of statusFilter) {
          try {
            chartersRes = await api.get('/api/v1/charters', { params: { status } })
            recovered = true
            break
          } catch (statusError) {
            // Try the next status filter.
          }
        }

        if (!recovered) {
          throw listError
        }
      }

      const clientsRes = await clientsPromise
      setCharters(chartersRes?.data ?? [])
      setClients(clientsRes.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load charters')
    } finally {
      setLoading(false)
    }
  }

  const getClientName = (clientId: number): string => {
    const client = clients.find(c => c.id === clientId)
    return client ? client.name : `Client #${clientId}`
  }

  const filteredCharters = charters.filter(charter => {
    const clientName = getClientName(charter.client_id).toLowerCase()
    const matchesClientName = filters.clientName === '' || clientName.includes(filters.clientName.toLowerCase())
    const matchesStatus = filters.status === '' || charter.status.toLowerCase().includes(filters.status.toLowerCase())
    const matchesMinCost = filters.minCost === '' || charter.total_cost >= parseFloat(filters.minCost)
    const matchesMaxCost = filters.maxCost === '' || charter.total_cost <= parseFloat(filters.maxCost)
    
    return matchesClientName && matchesStatus && matchesMinCost && matchesMaxCost
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed': return 'success'
      case 'pending': return 'warning'
      case 'quote': return 'info'
      case 'completed': return 'success'
      case 'cancelled': return 'error'
      default: return 'default'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Charters</Typography>
        <Button variant="contained" onClick={() => navigate('/charters/new')}>
          Create Charter
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>Filters</Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              size="small"
              label="Client Name"
              value={filters.clientName}
              onChange={(e) => setFilters({ ...filters, clientName: e.target.value })}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                )
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              size="small"
              label="Status"
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              placeholder="e.g., quote, booked"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              size="small"
              type="number"
              label="Min Cost"
              value={filters.minCost}
              onChange={(e) => setFilters({ ...filters, minCost: e.target.value })}
              InputProps={{ inputProps: { min: 0, step: 0.01 } }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              size="small"
              type="number"
              label="Max Cost"
              value={filters.maxCost}
              onChange={(e) => setFilters({ ...filters, maxCost: e.target.value })}
              InputProps={{ inputProps: { min: 0, step: 0.01 } }}
            />
          </Grid>
        </Grid>
      </Paper>

      <TableContainer component={Paper}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Client</TableCell>
                <TableCell>Vehicle</TableCell>
                <TableCell>Vendor</TableCell>
                <TableCell>Trip Date</TableCell>
                <TableCell>Passengers</TableCell>
                <TableCell>Hours</TableCell>
                <TableCell>Stops</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Total Cost</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredCharters.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={11} align="center">
                    <Typography color="textSecondary">No charters found</Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredCharters.map((charter) => (
                  <TableRow 
                    key={charter.id} 
                    hover
                    onDoubleClick={() => navigate(`/charters/${charter.id}`)}
                    sx={{ cursor: 'pointer' }}
                  >
                    <TableCell>{charter.id}</TableCell>
                    <TableCell>{getClientName(charter.client_id)}</TableCell>
                    <TableCell>{charter.vehicle?.name ?? `Vehicle #${charter.vehicle_id}`}</TableCell>
                    <TableCell>
                      {charter.vendor_name ? (
                        <Box>
                          <Typography variant="body2">{charter.vendor_name}</Typography>
                          <Typography variant="caption" color="textSecondary">{charter.vendor_email}</Typography>
                        </Box>
                      ) : (
                        <Typography variant="body2" color="textSecondary" fontStyle="italic">Unassigned</Typography>
                      )}
                    </TableCell>
                    <TableCell>{formatDate(charter.trip_date)}</TableCell>
                    <TableCell>{charter.passengers}</TableCell>
                    <TableCell>{charter.trip_hours}h</TableCell>
                    <TableCell>{charter.stops?.length ?? 0}</TableCell>
                    <TableCell>
                      <Chip label={charter.status} color={getStatusColor(charter.status)} size="small" />
                    </TableCell>
                    <TableCell>${(charter.total_cost ?? 0).toFixed(2)}</TableCell>
                    <TableCell>
                      <Button size="small" onClick={() => navigate(`/charters/${charter.id}`)}>
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        )}
      </TableContainer>
    </Box>
  )
}
