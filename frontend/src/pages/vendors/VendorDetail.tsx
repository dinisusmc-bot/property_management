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

interface Vendor {
  id: number
  email: string
  full_name: string
  role: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
  updated_at: string | null
}

interface Charter {
  id: number
  trip_date: string
  status: string
  total_cost: number
  vendor_total_cost?: number
  base_cost: number
  mileage_cost: number
  vendor_base_cost?: number
  vendor_mileage_cost?: number
  vendor_additional_fees?: number
  passengers: number
  pickup_location: string
  dropoff_location: string
  created_at: string
}

interface VendorPayment {
  id: number
  charter_id: number
  vendor_id: number
  amount: number
  payment_date: string | null
  payment_method: string | null
  payment_status: string
  reference_number: string | null
  notes: string | null
  created_at: string
}

export default function VendorDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [vendor, setVendor] = useState<Vendor | null>(null)
  const [charters, setCharters] = useState<Charter[]>([])
  const [payments, setPayments] = useState<VendorPayment[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingCharters, setLoadingCharters] = useState(true)
  const [loadingPayments, setLoadingPayments] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (id) {
      fetchVendor()
      fetchVendorCharters()
      fetchVendorPayments()
    }
  }, [id])

  const fetchVendor = async () => {
    try {
      setLoading(true)
      const response = await api.get(`/api/v1/auth/users/${id}`)
      setVendor(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load vendor')
    } finally {
      setLoading(false)
    }
  }

  const fetchVendorCharters = async () => {
    try {
      setLoadingCharters(true)
      const response = await api.get('/api/v1/charters', {
        params: { vendor_id: id }
      })
      setCharters(response.data)
    } catch (err: any) {
      console.error('Failed to load vendor charters:', err)
    } finally {
      setLoadingCharters(false)
    }
  }

  const fetchVendorPayments = async () => {
    try {
      setLoadingPayments(true)
      const response = await api.get('/api/v1/charters/vendor-payments', {
        params: { vendor_id: id }
      })
      setPayments(response.data)
    } catch (err: any) {
      console.error('Failed to load vendor payments:', err)
    } finally {
      setLoadingPayments(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'quote': return 'default'
      case 'approved': return 'info'
      case 'booked': return 'primary'
      case 'confirmed': return 'success'
      case 'in_progress': return 'warning'
      case 'completed': return 'success'
      case 'cancelled': return 'error'
      default: return 'default'
    }
  }

  const calculateTotalBookings = () => {
    return charters.filter(c => ['booked', 'confirmed', 'in_progress', 'completed'].includes(c.status)).length
  }

  const calculateTotalOwed = () => {
    return charters.reduce((sum, c) => {
      const vendorTotal = c.vendor_total_cost ?? 
        ((c.vendor_base_cost ?? c.base_cost * 0.75) + 
         (c.vendor_mileage_cost ?? c.mileage_cost * 0.75) + 
         (c.vendor_additional_fees ?? 0))
      return sum + vendorTotal
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
        <Button onClick={() => navigate('/vendors')} sx={{ mt: 2 }}>
          Back to Vendors
        </Button>
      </Box>
    )
  }

  if (!vendor) {
    return (
      <Box>
        <Alert severity="warning">Vendor not found</Alert>
        <Button onClick={() => navigate('/vendors')} sx={{ mt: 2 }}>
          Back to Vendors
        </Button>
      </Box>
    )
  }

  return (
    <Box>
      <Button
        startIcon={<BackIcon />}
        onClick={() => navigate('/vendors')}
        sx={{ mb: 2 }}
      >
        Back to Vendors
      </Button>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">{vendor.full_name}</Typography>
        <Chip 
          label={vendor.is_active ? 'Active' : 'Inactive'} 
          color={vendor.is_active ? 'success' : 'default'} 
        />
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Vendor Information
            </Typography>
            <Divider sx={{ mb: 2 }} />

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Email</Typography>
              <Typography variant="body1">{vendor.email}</Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Role</Typography>
              <Box sx={{ mt: 0.5 }}>
                <Chip label={vendor.role} color="primary" size="small" />
              </Box>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Created</Typography>
              <Typography variant="body1">
                {new Date(vendor.created_at).toLocaleDateString()}
              </Typography>
            </Box>

            {vendor.updated_at && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="caption" color="textSecondary">Last Updated</Typography>
                <Typography variant="body1">
                  {new Date(vendor.updated_at).toLocaleDateString()}
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Payment Status
            </Typography>
            <Divider sx={{ mb: 2 }} />

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Total Owed</Typography>
              <Typography variant="h4" color="error.main">
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
              <Typography variant="h4" color="warning.main">
                ${calculateOutstandingBalance().toFixed(2)}
              </Typography>
            </Box>
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
                  label={`$${calculateTotalPaid().toFixed(2)} Paid`} 
                  color="success"
                />
              </Box>
            </Box>
            <Divider sx={{ mb: 2 }} />
            
            {loadingPayments ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
              </Box>
            ) : payments.length === 0 ? (
              <Alert severity="info">No payments recorded for this vendor</Alert>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Payment ID</TableCell>
                      <TableCell>Charter ID</TableCell>
                      <TableCell>Amount</TableCell>
                      <TableCell>Payment Date</TableCell>
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

        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Booking History
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                <Chip 
                  label={`${charters.length} Total Orders`} 
                  color="primary" 
                  variant="outlined"
                />
                <Chip 
                  label={`${calculateTotalBookings()} Bookings`} 
                  color="success"
                  variant="outlined"
                />
              </Box>
            </Box>
            <Divider sx={{ mb: 2 }} />
            
            {loadingCharters ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
              </Box>
            ) : charters.length === 0 ? (
              <Alert severity="info">No bookings found for this vendor</Alert>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Order ID</TableCell>
                      <TableCell>Trip Date</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Passengers</TableCell>
                      <TableCell>Route</TableCell>
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
                        <TableCell>
                          <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                            {charter.pickup_location} → {charter.dropoff_location}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          ${(() => {
                            const vendorTotal = charter.vendor_total_cost ?? 
                              ((charter.vendor_base_cost ?? charter.base_cost * 0.75) + 
                               (charter.vendor_mileage_cost ?? charter.mileage_cost * 0.75) + 
                               (charter.vendor_additional_fees ?? 0))
                            return vendorTotal.toFixed(2)
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
      </Grid>
    </Box>
  )
}
