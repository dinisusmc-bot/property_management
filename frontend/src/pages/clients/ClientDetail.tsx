import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Typography,
  Paper,
  Box,
  Grid,
  Button,
  Chip,
  CircularProgress,
  Alert,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material'
import { ArrowBack as BackIcon } from '@mui/icons-material'
import api from '../../services/api'

interface Client {
  id: number
  name: string
  type: string
  email: string
  phone: string
  address: string
  city: string
  state: string
  zip_code: string
  notes: string | null
  credit_limit: number
  balance_owed: number
  is_active: boolean
  created_at: string
  updated_at: string | null
}

interface Charter {
  id: number
  trip_date: string
  status: string
  total_cost: number
  client_total_charge?: number
  base_cost: number
  mileage_cost: number
  client_base_charge?: number
  client_mileage_charge?: number
  client_additional_fees?: number
  passengers: number
  created_at: string
}

interface ClientPayment {
  id: number
  charter_id: number
  client_id: number
  amount: number
  payment_date: string | null
  payment_method: string | null
  payment_status: string
  payment_type: string | null
  reference_number: string | null
  notes: string | null
  created_at: string
}

export default function ClientDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [client, setClient] = useState<Client | null>(null)
  const [charters, setCharters] = useState<Charter[]>([])
  const [payments, setPayments] = useState<ClientPayment[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingCharters, setLoadingCharters] = useState(true)
  const [loadingPayments, setLoadingPayments] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (id) {
      fetchClient()
      fetchClientCharters()
      fetchClientPayments()
    }
  }, [id])

  const fetchClient = async () => {
    try {
      setLoading(true)
      const response = await api.get(`/api/v1/clients/${id}`)
      setClient(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load client')
    } finally {
      setLoading(false)
    }
  }

  const fetchClientCharters = async () => {
    try {
      setLoadingCharters(true)
      const response = await api.get('/api/v1/charters', {
        params: { client_id: id }
      })
      setCharters(response.data)
    } catch (err: any) {
      console.error('Failed to load client charters:', err)
      console.error('Error details:', err.response?.data, err.response?.status)
    } finally {
      setLoadingCharters(false)
    }
  }

  const fetchClientPayments = async () => {
    try {
      setLoadingPayments(true)
      const response = await api.get('/api/v1/charters/client-payments', {
        params: { client_id: id }
      })
      setPayments(response.data)
    } catch (err: any) {
      console.error('Failed to load client payments:', err)
    } finally {
      setLoadingPayments(false)
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'corporate': return 'primary'
      case 'personal': return 'success'
      case 'government': return 'info'
      default: return 'default'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'quote': return 'default'
      case 'confirmed': return 'info'
      case 'in_progress': return 'warning'
      case 'completed': return 'success'
      case 'cancelled': return 'error'
      default: return 'default'
    }
  }

  const calculateTotalOwed = () => {
    return charters.reduce((sum, c) => {
      const clientTotal = c.client_total_charge ?? 
        ((c.client_base_charge ?? c.base_cost) + 
         (c.client_mileage_charge ?? c.mileage_cost) + 
         (c.client_additional_fees ?? 0))
      return sum + clientTotal
    }, 0)
  }

  const calculateTotalPaid = () => {
    return payments
      .filter(p => p.payment_status === 'paid')
      .reduce((sum, p) => sum + p.amount, 0)
  }

  const calculateOutstandingBalance = () => {
    return calculateTotalOwed() - calculateTotalPaid()
  }

  const getPaymentStatusColor = (status: string) => {
    switch (status) {
      case 'paid': return 'success'
      case 'pending': return 'warning'
      case 'partial': return 'info'
      case 'cancelled': return 'error'
      default: return 'default'
    }
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Box>
        <Alert severity="error">{error}</Alert>
        <Button onClick={() => navigate('/clients')} sx={{ mt: 2 }}>
          Back to Clients
        </Button>
      </Box>
    )
  }

  if (!client) {
    return (
      <Box>
        <Alert severity="warning">Client not found</Alert>
        <Button onClick={() => navigate('/clients')} sx={{ mt: 2 }}>
          Back to Clients
        </Button>
      </Box>
    )
  }

  return (
    <Box>
      <Button
        startIcon={<BackIcon />}
        onClick={() => navigate('/clients')}
        sx={{ mb: 2 }}
      >
        Back to Clients
      </Button>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">{client.name}</Typography>
        <Chip 
          label={client.is_active ? 'Active' : 'Inactive'} 
          color={client.is_active ? 'success' : 'default'} 
        />
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Contact Information
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Type</Typography>
              <Box sx={{ mt: 0.5 }}>
                <Chip label={client.type} color={getTypeColor(client.type)} size="small" />
              </Box>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Email</Typography>
              <Typography variant="body1">{client.email}</Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Phone</Typography>
              <Typography variant="body1">{client.phone}</Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Address</Typography>
              <Typography variant="body1">{client.address}</Typography>
              <Typography variant="body1">
                {client.city}, {client.state} {client.zip_code}
              </Typography>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Payment Status
            </Typography>
            <Divider sx={{ mb: 2 }} />

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Total Charges</Typography>
              <Typography variant="h4" color="primary.main">
                ${calculateTotalOwed().toFixed(2)}
              </Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Total Paid</Typography>
              <Typography variant="h4" color="success.main">
                ${calculateTotalPaid().toFixed(2)}
              </Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Outstanding Balance</Typography>
              <Typography variant="h4" color={calculateOutstandingBalance() > 0 ? 'error.main' : 'success.main'}>
                ${calculateOutstandingBalance().toFixed(2)}
              </Typography>
            </Box>
          </Paper>
        </Grid>

        {client.notes && (
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Notes
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Typography variant="body1">{client.notes}</Typography>
            </Paper>
          </Grid>
        )}

        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Order History
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                <Chip 
                  label={`${charters.length} Total Orders`} 
                  color="primary" 
                  variant="outlined"
                />
                <Chip 
                  label={`$${calculateTotalOwed().toFixed(2)} Total Charges`} 
                  color="success"
                />
              </Box>
            </Box>
            <Divider sx={{ mb: 2 }} />
            
            {loadingCharters ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
              </Box>
            ) : charters.length === 0 ? (
              <Alert severity="info">No orders found for this client</Alert>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Order ID</TableCell>
                      <TableCell>Trip Date</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Passengers</TableCell>
                      <TableCell align="right">Total Cost</TableCell>
                      <TableCell>Created</TableCell>
                      <TableCell align="center">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {charters.map((charter) => (
                      <TableRow 
                        key={charter.id} 
                        hover
                        onDoubleClick={() => navigate(`/charters/${charter.id}`)}
                        sx={{ cursor: 'pointer' }}
                      >
                        <TableCell>#{charter.id}</TableCell>
                        <TableCell>
                          {new Date(charter.trip_date).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={charter.status} 
                            color={getStatusColor(charter.status)} 
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{charter.passengers}</TableCell>
                        <TableCell align="right">
                          ${(() => {
                            const clientTotal = charter.client_total_charge ?? 
                              ((charter.client_base_charge ?? charter.base_cost) + 
                               (charter.client_mileage_charge ?? charter.mileage_cost) + 
                               (charter.client_additional_fees ?? 0))
                            return clientTotal.toFixed(2)
                          })()}
                        </TableCell>
                        <TableCell>
                          {new Date(charter.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell align="center">
                          <Button
                            size="small"
                            variant="outlined"
                            onClick={() => navigate(`/charters/${charter.id}`)}
                          >
                            View
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Paper>
        </Grid>

        {/* Payments Section */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Payment History
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                <Chip 
                  label={`${payments.length} Payments`} 
                  color="primary" 
                  variant="outlined"
                />
                <Chip 
                  label={`$${calculateTotalPaid().toFixed(2)} Received`} 
                  color="success"
                />
                <Chip 
                  label={`$${calculateOutstandingBalance().toFixed(2)} Outstanding`} 
                  color={calculateOutstandingBalance() > 0 ? 'error' : 'success'}
                />
              </Box>
            </Box>
            <Divider sx={{ mb: 2 }} />
            
            {loadingPayments ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
              </Box>
            ) : payments.length === 0 ? (
              <Alert severity="info">No payments recorded for this client</Alert>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Payment ID</TableCell>
                      <TableCell>Charter ID</TableCell>
                      <TableCell>Amount</TableCell>
                      <TableCell>Payment Date</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Method</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Reference</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {payments.map((payment) => (
                      <TableRow key={payment.id} hover>
                        <TableCell>#{payment.id}</TableCell>
                        <TableCell>
                          <Button
                            size="small"
                            onClick={() => navigate(`/charters/${payment.charter_id}`)}
                          >
                            #{payment.charter_id}
                          </Button>
                        </TableCell>
                        <TableCell>${payment.amount.toFixed(2)}</TableCell>
                        <TableCell>
                          {payment.payment_date 
                            ? new Date(payment.payment_date).toLocaleDateString()
                            : 'Not set'}
                        </TableCell>
                        <TableCell>
                          {payment.payment_type || 'N/A'}
                        </TableCell>
                        <TableCell>
                          {payment.payment_method || 'N/A'}
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={payment.payment_status} 
                            color={getPaymentStatusColor(payment.payment_status)} 
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{payment.reference_number || '-'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
