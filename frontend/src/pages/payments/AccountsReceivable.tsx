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
  Grid,
  Card,
  CardContent,
  TextField,
} from '@mui/material'
import { useNavigate } from 'react-router-dom'
import api from '../../services/api'
import {
  Receipt as InvoiceIcon,
  AccountBalance as BalanceIcon,
  CheckCircle as PaidIcon,
  Warning as OverdueIcon,
} from '@mui/icons-material'

interface Charter {
  id: number
  client_id: number
  trip_date: string
  status: string
  passengers: number
  client_total_charge: number | null
  total_cost: number
  base_cost: number
  mileage_cost: number
  additional_fees: number | null
  client_base_charge: number | null
  client_mileage_charge: number | null
  client_additional_fees: number | null
  created_at: string
}

interface ClientPayment {
  id: number
  charter_id: number
  amount: number
  payment_status: string
  payment_date: string | null
}

interface Client {
  id: number
  company_name?: string
  first_name?: string
  last_name?: string
  email: string
}

export default function AccountsReceivable() {
  const navigate = useNavigate()
  const [charters, setCharters] = useState<Charter[]>([])
  const [payments, setPayments] = useState<ClientPayment[]>([])
  const [clients, setClients] = useState<Map<number, Client>>(new Map())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const [chartersResponse, paymentsResponse, clientsResponse] = await Promise.all([
        api.get('/api/v1/charters/charters'),
        api.get('/api/v1/charters/client-payments'),
        api.get('/api/v1/clients/clients')
      ])
      
      // Handle response data - it might be nested in a data property
      const chartersData = Array.isArray(chartersResponse.data) ? chartersResponse.data : []
      const paymentsData = Array.isArray(paymentsResponse.data) ? paymentsResponse.data : []
      const clientsData = Array.isArray(clientsResponse.data) ? clientsResponse.data : []
      
      // Filter to only approved/booked/in_progress/completed charters
      const relevantCharters = chartersData.filter((c: Charter) => 
        ['quote_approved', 'booked', 'confirmed', 'in_progress', 'completed'].includes(c.status)
      )
      
      setCharters(relevantCharters)
      setPayments(paymentsData)
      
      // Create client lookup map
      const clientMap = new Map()
      clientsData.forEach((client: Client) => {
        clientMap.set(client.id, client)
      })
      setClients(clientMap)
    } catch (err: any) {
      setError('Failed to load accounts receivable data')
      console.error('Error loading AR data:', err)
    } finally {
      setLoading(false)
    }
  }

  const calculateCharterAmount = (charter: Charter): number => {
    // Always calculate from components to ensure all fees are included
    const baseCharge = charter.client_base_charge ?? charter.base_cost ?? 0
    const mileageCharge = charter.client_mileage_charge ?? charter.mileage_cost ?? 0
    const additionalFees = charter.client_additional_fees ?? charter.additional_fees ?? 0
    
    return baseCharge + mileageCharge + additionalFees
  }

  const getPaymentsForCharter = (charterId: number) => {
    return payments.filter(p => p.charter_id === charterId)
  }

  const calculatePaidAmount = (charterId: number): number => {
    return getPaymentsForCharter(charterId)
      .filter(p => p.payment_status === 'paid')
      .reduce((sum, p) => sum + p.amount, 0)
  }

  const calculateBalance = (charter: Charter): number => {
    const invoiceAmount = calculateCharterAmount(charter)
    const paidAmount = calculatePaidAmount(charter.id)
    return invoiceAmount - paidAmount
  }

  const getStatusColor = (status: string): 'default' | 'primary' | 'success' | 'warning' | 'error' => {
    switch (status) {
      case 'completed':
        return 'success'
      case 'in_progress':
        return 'primary'
      case 'booked':
      case 'confirmed':
        return 'warning'
      default:
        return 'default'
    }
  }

  const getClientName = (clientId: number): string => {
    const client = clients.get(clientId)
    if (!client) return `Client #${clientId}`
    return client.company_name || `${client.first_name || ''} ${client.last_name || ''}`.trim()
  }

  const isOverdue = (charter: Charter): boolean => {
    const balance = calculateBalance(charter)
    const tripDate = new Date(charter.trip_date)
    const daysAfterTrip = Math.floor((Date.now() - tripDate.getTime()) / (1000 * 60 * 60 * 24))
    return balance > 0 && charter.status === 'completed' && daysAfterTrip > 30
  }

  const filteredCharters = charters.filter(charter => {
    const balance = calculateBalance(charter)
    if (statusFilter === 'outstanding' && balance <= 0) return false
    if (statusFilter === 'paid' && balance > 0) return false
    if (statusFilter === 'overdue' && !isOverdue(charter)) return false
    
    if (searchTerm) {
      const clientName = getClientName(charter.client_id).toLowerCase()
      const search = searchTerm.toLowerCase()
      if (!clientName.includes(search) && !charter.id.toString().includes(search)) {
        return false
      }
    }
    
    return true
  })

  const totalInvoiced = filteredCharters.reduce((sum, c) => sum + calculateCharterAmount(c), 0)
  const totalPaid = filteredCharters.reduce((sum, c) => sum + calculatePaidAmount(c.id), 0)
  const totalOutstanding = totalInvoiced - totalPaid
  const overdueCount = charters.filter(c => isOverdue(c)).length

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
          Accounts Receivable
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Summary Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <InvoiceIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="subtitle2" color="text.secondary">
                  Total Invoiced
                </Typography>
              </Box>
              <Typography variant="h5">${totalInvoiced.toFixed(2)}</Typography>
              <Typography variant="caption" color="text.secondary">
                {filteredCharters.length} invoices
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <PaidIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="subtitle2" color="text.secondary">
                  Total Paid
                </Typography>
              </Box>
              <Typography variant="h5" color="success.main">
                ${totalPaid.toFixed(2)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {((totalPaid / totalInvoiced) * 100 || 0).toFixed(1)}% collected
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <BalanceIcon color="warning" sx={{ mr: 1 }} />
                <Typography variant="subtitle2" color="text.secondary">
                  Outstanding Balance
                </Typography>
              </Box>
              <Typography variant="h5" color="warning.main">
                ${totalOutstanding.toFixed(2)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {filteredCharters.filter(c => calculateBalance(c) > 0).length} unpaid
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <OverdueIcon color="error" sx={{ mr: 1 }} />
                <Typography variant="subtitle2" color="text.secondary">
                  Overdue (30+ days)
                </Typography>
              </Box>
              <Typography variant="h5" color="error.main">
                {overdueCount}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Requires attention
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              size="small"
              label="Search Client or Charter #"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box display="flex" gap={1}>
              <Button
                size="small"
                variant={statusFilter === 'all' ? 'contained' : 'outlined'}
                onClick={() => setStatusFilter('all')}
              >
                All
              </Button>
              <Button
                size="small"
                variant={statusFilter === 'outstanding' ? 'contained' : 'outlined'}
                color="warning"
                onClick={() => setStatusFilter('outstanding')}
              >
                Outstanding
              </Button>
              <Button
                size="small"
                variant={statusFilter === 'paid' ? 'contained' : 'outlined'}
                color="success"
                onClick={() => setStatusFilter('paid')}
              >
                Paid
              </Button>
              <Button
                size="small"
                variant={statusFilter === 'overdue' ? 'contained' : 'outlined'}
                color="error"
                onClick={() => setStatusFilter('overdue')}
              >
                Overdue
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Invoices Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Charter #</TableCell>
              <TableCell>Client</TableCell>
              <TableCell>Service Date</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Invoice Amount</TableCell>
              <TableCell align="right">Paid</TableCell>
              <TableCell align="right">Balance Due</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredCharters.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <Typography color="text.secondary" py={3}>
                    No receivables found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredCharters
                .sort((a, b) => new Date(b.trip_date).getTime() - new Date(a.trip_date).getTime())
                .map((charter) => {
                  const invoiceAmount = calculateCharterAmount(charter)
                  const paidAmount = calculatePaidAmount(charter.id)
                  const balance = invoiceAmount - paidAmount
                  const overdue = isOverdue(charter)

                  return (
                    <TableRow 
                      key={charter.id}
                      hover
                      onDoubleClick={() => navigate(`/charters/${charter.id}`)}
                      sx={{ 
                        cursor: 'pointer',
                        bgcolor: overdue ? 'error.50' : 'inherit'
                      }}
                    >
                      <TableCell>
                        <Chip 
                          label={`#${charter.id}`} 
                          size="small" 
                          color="primary"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Button
                          size="small"
                          variant="text"
                          onClick={(e) => {
                            e.stopPropagation()
                            navigate(`/clients/${charter.client_id}`)
                          }}
                        >
                          {getClientName(charter.client_id)}
                        </Button>
                      </TableCell>
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
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight="medium">
                          ${invoiceAmount.toFixed(2)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" color="success.main">
                          ${paidAmount.toFixed(2)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography 
                          variant="body2" 
                          fontWeight="bold"
                          color={balance > 0 ? (overdue ? 'error.main' : 'warning.main') : 'success.main'}
                        >
                          ${balance.toFixed(2)}
                          {overdue && <Chip label="OVERDUE" size="small" color="error" sx={{ ml: 1 }} />}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={(e) => {
                            e.stopPropagation()
                            navigate(`/charters/${charter.id}`)
                          }}
                        >
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  )
                })
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}
