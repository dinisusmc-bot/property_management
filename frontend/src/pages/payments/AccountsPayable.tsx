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
  Receipt as BillIcon,
  AccountBalance as BalanceIcon,
  CheckCircle as PaidIcon,
  Warning as OverdueIcon,
} from '@mui/icons-material'

interface Charter {
  id: number
  vendor_id: number | null
  trip_date: string
  status: string
  passengers: number
  vendor_total_cost: number | null
  total_cost: number
  base_cost: number
  mileage_cost: number
  additional_fees: number | null
  vendor_base_cost: number | null
  vendor_mileage_cost: number | null
  vendor_additional_fees: number | null
  created_at: string
}

interface VendorPayment {
  id: number
  charter_id: number
  amount: number
  payment_status: string
  payment_date: string | null
}

interface Vendor {
  id: number
  name?: string
  email: string
}

export default function AccountsPayable() {
  const navigate = useNavigate()
  const [charters, setCharters] = useState<Charter[]>([])
  const [payments, setPayments] = useState<VendorPayment[]>([])
  const [vendors, setVendors] = useState<Map<number, Vendor>>(new Map())
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
      const [chartersResponse, paymentsResponse, vendorsResponse] = await Promise.all([
        api.get('/api/v1/charters/charters'),
        api.get('/api/v1/charters/vendor-payments'),
        api.get('/api/v1/auth/vendors')
      ])
      
      // Handle response data - it might be nested in a data property
      const chartersData = Array.isArray(chartersResponse.data) ? chartersResponse.data : []
      const paymentsData = Array.isArray(paymentsResponse.data) ? paymentsResponse.data : []
      const vendorsData = Array.isArray(vendorsResponse.data) ? vendorsResponse.data : []
      
      // Filter to only booked/confirmed/in_progress/completed charters with vendors
      const relevantCharters = chartersData.filter((c: Charter) => 
        c.vendor_id && ['booked', 'confirmed', 'in_progress', 'completed'].includes(c.status)
      )
      
      setCharters(relevantCharters)
      setPayments(paymentsData)
      
      // Create vendor lookup map
      const vendorMap = new Map()
      vendorsData.forEach((vendor: Vendor) => {
        vendorMap.set(vendor.id, vendor)
      })
      setVendors(vendorMap)
    } catch (err: any) {
      setError('Failed to load accounts payable data')
      console.error('Error loading AP data:', err)
    } finally {
      setLoading(false)
    }
  }

  const calculateCharterCost = (charter: Charter): number => {
    // Always calculate from components to ensure all fees are included
    const baseCost = charter.vendor_base_cost ?? (charter.base_cost ? charter.base_cost * 0.75 : 0)
    const mileageCost = charter.vendor_mileage_cost ?? (charter.mileage_cost ? charter.mileage_cost * 0.75 : 0)
    const additionalFees = charter.vendor_additional_fees ?? charter.additional_fees ?? 0
    
    return baseCost + mileageCost + additionalFees
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
    const billAmount = calculateCharterCost(charter)
    const paidAmount = calculatePaidAmount(charter.id)
    return billAmount - paidAmount
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

  const getVendorName = (vendorId: number | null): string => {
    if (!vendorId) return 'No Vendor'
    const vendor = vendors.get(vendorId)
    if (!vendor) return `Vendor #${vendorId}`
    return vendor.name || vendor.email
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
      const vendorName = getVendorName(charter.vendor_id).toLowerCase()
      const search = searchTerm.toLowerCase()
      if (!vendorName.includes(search) && !charter.id.toString().includes(search)) {
        return false
      }
    }
    
    return true
  })

  const totalBilled = filteredCharters.reduce((sum, c) => sum + calculateCharterCost(c), 0)
  const totalPaid = filteredCharters.reduce((sum, c) => sum + calculatePaidAmount(c.id), 0)
  const totalOutstanding = totalBilled - totalPaid
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
          Accounts Payable
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
                <BillIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="subtitle2" color="text.secondary">
                  Total Billed
                </Typography>
              </Box>
              <Typography variant="h5">${totalBilled.toFixed(2)}</Typography>
              <Typography variant="caption" color="text.secondary">
                {filteredCharters.length} bills
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
                {((totalPaid / totalBilled) * 100 || 0).toFixed(1)}% paid
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <BalanceIcon color="error" sx={{ mr: 1 }} />
                <Typography variant="subtitle2" color="text.secondary">
                  Outstanding Balance
                </Typography>
              </Box>
              <Typography variant="h5" color="error.main">
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
                Requires payment
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
              label="Search Vendor or Charter #"
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
                color="error"
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

      {/* Bills Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Charter #</TableCell>
              <TableCell>Vendor</TableCell>
              <TableCell>Service Date</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Bill Amount</TableCell>
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
                    No payables found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredCharters
                .sort((a, b) => new Date(b.trip_date).getTime() - new Date(a.trip_date).getTime())
                .map((charter) => {
                  const billAmount = calculateCharterCost(charter)
                  const paidAmount = calculatePaidAmount(charter.id)
                  const balance = billAmount - paidAmount
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
                            navigate(`/vendors/${charter.vendor_id}`)
                          }}
                        >
                          {getVendorName(charter.vendor_id)}
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
                          ${billAmount.toFixed(2)}
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
                          color={balance > 0 ? (overdue ? 'error.main' : 'error.dark') : 'success.main'}
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
