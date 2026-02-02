import { useState, useEffect } from 'react'
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Chip,
  CircularProgress,
  Alert,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Grid,
  Card,
  CardContent,
  Tabs,
  Tab,
} from '@mui/material'
import { useNavigate } from 'react-router-dom'
import api from '../../services/api'
import {
  Payments as PaymentsIcon,
  TrendingUp as RevenueIcon,
  TrendingDown as ExpenseIcon,
  AccountBalance as BalanceIcon,
} from '@mui/icons-material'

interface Payment {
  id: number
  type: 'vendor' | 'client'
  charter_id: number
  vendor_id?: number
  client_id?: number
  vendor_name?: string
  client_name?: string
  amount: number
  payment_date: string | null
  payment_method: string | null
  payment_status: string
  payment_type?: string | null
  reference_number: string | null
  notes: string | null
  created_at: string
}

export default function PaymentsList() {
  const navigate = useNavigate()
  const [vendorPayments, setVendorPayments] = useState<Payment[]>([])
  const [clientPayments, setClientPayments] = useState<Payment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tabValue, setTabValue] = useState(0)
  
  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [methodFilter, setMethodFilter] = useState<string>('all')
  const [dateFrom, setDateFrom] = useState<string>('')
  const [dateTo, setDateTo] = useState<string>('')

  useEffect(() => {
    fetchPayments()
  }, [])

  const fetchPayments = async () => {
    try {
      setLoading(true)
      const [vendorResponse, clientResponse] = await Promise.all([
        api.get('/api/v1/charters/vendor-payments'),
        api.get('/api/v1/charters/client-payments')
      ])
      
      const vendorPaymentsData = vendorResponse.data.map((p: any) => ({ ...p, type: 'vendor' as const }))
      const clientPaymentsData = clientResponse.data.map((p: any) => ({ ...p, type: 'client' as const }))
      
      setVendorPayments(vendorPaymentsData)
      setClientPayments(clientPaymentsData)
    } catch (err: any) {
      setError('Failed to load payments')
      console.error('Error loading payments:', err)
    } finally {
      setLoading(false)
    }
  }

  const getPaymentStatusColor = (status: string): 'success' | 'warning' | 'error' | 'default' => {
    switch (status) {
      case 'paid':
        return 'success'
      case 'pending':
      case 'partial':
        return 'warning'
      case 'cancelled':
        return 'error'
      default:
        return 'default'
    }
  }

  const getPaymentMethodLabel = (method: string | null): string => {
    if (!method) return 'N/A'
    return method.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')
  }

  const filterPayments = (payments: Payment[]) => {
    return payments.filter(payment => {
      if (statusFilter !== 'all' && payment.payment_status !== statusFilter) return false
      if (methodFilter !== 'all' && payment.payment_method !== methodFilter) return false
      if (dateFrom && payment.payment_date && payment.payment_date < dateFrom) return false
      if (dateTo && payment.payment_date && payment.payment_date > dateTo) return false
      return true
    })
  }

  const calculateTotals = (payments: Payment[]) => {
    const filtered = filterPayments(payments)
    return {
      total: filtered.reduce((sum, p) => sum + p.amount, 0),
      paid: filtered.filter(p => p.payment_status === 'paid').reduce((sum, p) => sum + p.amount, 0),
      pending: filtered.filter(p => p.payment_status === 'pending').reduce((sum, p) => sum + p.amount, 0),
      count: filtered.length
    }
  }

  const vendorTotals = calculateTotals(vendorPayments)
  const clientTotals = calculateTotals(clientPayments)
  const netProfit = clientTotals.paid - vendorTotals.paid

  const currentPayments = tabValue === 0 ? clientPayments : vendorPayments
  const filteredPayments = filterPayments(currentPayments)

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Payment Transactions
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Summary Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <RevenueIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="subtitle2" color="text.secondary">
                  To Receive (Pending)
                </Typography>
              </Box>
              <Typography variant="h5" color="success.main">
                ${clientTotals.pending.toFixed(2)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                ${clientTotals.paid.toFixed(2)} received
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <ExpenseIcon color="error" sx={{ mr: 1 }} />
                <Typography variant="subtitle2" color="text.secondary">
                  To Pay (Pending)
                </Typography>
              </Box>
              <Typography variant="h5" color="error.main">
                ${vendorTotals.pending.toFixed(2)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                ${vendorTotals.paid.toFixed(2)} paid
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <BalanceIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="subtitle2" color="text.secondary">
                  Net Profit
                </Typography>
              </Box>
              <Typography variant="h5" color={netProfit >= 0 ? 'success.main' : 'error.main'}>
                ${netProfit.toFixed(2)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                From paid transactions
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <PaymentsIcon color="info" sx={{ mr: 1 }} />
                <Typography variant="subtitle2" color="text.secondary">
                  Total Payments
                </Typography>
              </Box>
              <Typography variant="h5">
                {vendorPayments.length + clientPayments.length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {vendorPayments.length} vendor / {clientPayments.length} client
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                label="Status"
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <MenuItem value="all">All Status</MenuItem>
                <MenuItem value="pending">Pending</MenuItem>
                <MenuItem value="paid">Paid</MenuItem>
                <MenuItem value="partial">Partial</MenuItem>
                <MenuItem value="cancelled">Cancelled</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Payment Method</InputLabel>
              <Select
                value={methodFilter}
                label="Payment Method"
                onChange={(e) => setMethodFilter(e.target.value)}
              >
                <MenuItem value="all">All Methods</MenuItem>
                <MenuItem value="check">Check</MenuItem>
                <MenuItem value="wire_transfer">Wire Transfer</MenuItem>
                <MenuItem value="ach">ACH</MenuItem>
                <MenuItem value="credit_card">Credit Card</MenuItem>
                <MenuItem value="cash">Cash</MenuItem>
                <MenuItem value="invoice">Invoice</MenuItem>
                <MenuItem value="other">Other</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              size="small"
              label="From Date"
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              size="small"
              label="To Date"
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label={`Client Payments (${filterPayments(clientPayments).length})`} />
          <Tab label={`Vendor Payments (${filterPayments(vendorPayments).length})`} />
        </Tabs>
      </Box>

      {/* Payments Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Payment ID</TableCell>
              <TableCell>Charter ID</TableCell>
              <TableCell>{tabValue === 0 ? 'Client' : 'Vendor'}</TableCell>
              <TableCell align="right">Amount</TableCell>
              <TableCell>Payment Date</TableCell>
              <TableCell>Method</TableCell>
              <TableCell>Status</TableCell>
              {tabValue === 0 && <TableCell>Type</TableCell>}
              <TableCell>Reference</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredPayments.length === 0 ? (
              <TableRow>
                <TableCell colSpan={tabValue === 0 ? 10 : 9} align="center">
                  <Typography color="text.secondary" py={3}>
                    No payments found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredPayments
                .sort((a: Payment, b: Payment) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
                .map((payment: Payment) => (
                  <TableRow 
                    key={`${payment.type}-${payment.id}`}
                    hover
                    onDoubleClick={() => navigate(`/payments/${payment.type}/${payment.id}`)}
                    sx={{ cursor: 'pointer' }}
                  >
                    <TableCell>
                      <Chip 
                        label={`#${payment.id}`} 
                        size="small" 
                        color={payment.type === 'client' ? 'success' : 'warning'}
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Button
                        size="small"
                        variant="text"
                        onClick={(e) => {
                          e.stopPropagation()
                          navigate(`/charters/${payment.charter_id}`)
                        }}
                      >
                        #{payment.charter_id}
                      </Button>
                    </TableCell>
                    <TableCell>
                      {payment.type === 'client' ? payment.client_name || `Client #${payment.client_id}` : payment.vendor_name || `Vendor #${payment.vendor_id}`}
                    </TableCell>
                    <TableCell align="right">
                      <Typography 
                        variant="body2" 
                        fontWeight="medium"
                        color={payment.type === 'client' ? 'success.main' : 'error.main'}
                      >
                        ${payment.amount.toFixed(2)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {payment.payment_date 
                        ? new Date(payment.payment_date).toLocaleDateString() 
                        : <Chip label="Not Set" size="small" variant="outlined" />
                      }
                    </TableCell>
                    <TableCell>
                      {payment.payment_method 
                        ? <Chip label={getPaymentMethodLabel(payment.payment_method)} size="small" variant="outlined" />
                        : 'N/A'
                      }
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={payment.payment_status} 
                        color={getPaymentStatusColor(payment.payment_status)} 
                        size="small"
                      />
                    </TableCell>
                    {tabValue === 0 && (
                      <TableCell>
                        {payment.payment_type 
                          ? <Chip label={getPaymentMethodLabel(payment.payment_type)} size="small" variant="outlined" />
                          : 'N/A'
                        }
                      </TableCell>
                    )}
                    <TableCell>
                      {payment.reference_number || '-'}
                    </TableCell>
                    <TableCell align="center">
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={(e) => {
                          e.stopPropagation()
                          navigate(`/payments/${payment.type}/${payment.id}`)
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
