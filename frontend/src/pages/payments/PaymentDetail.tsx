import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  CircularProgress,
  Alert,
  Grid,
  Card,
  CardContent,
  Chip,
  Button,
  Divider,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../../services/api'
import {
  ArrowBack,
  Edit,
  Receipt,
  Person,
  Business,
  Payment as PaymentIcon,
} from '@mui/icons-material'

interface Payment {
  id: number
  charter_id: number
  vendor_id?: number
  client_id?: number
  amount: number
  payment_date: string | null
  payment_method: string | null
  payment_status: string
  payment_type?: string | null
  reference_number: string | null
  notes: string | null
  created_at: string
  updated_at: string | null
  created_by: number | null
}

interface Charter {
  id: number
  trip_date: string
  status: string
  passengers: number
  pickup_location?: string
  dropoff_location?: string
  total_cost: number
  vendor_total_cost?: number
  client_total_charge?: number
}

interface Entity {
  id: number
  name?: string
  email?: string
  company_name?: string
  first_name?: string
  last_name?: string
}

export default function PaymentDetail() {
  const { type, id } = useParams<{ type: 'vendor' | 'client'; id: string }>()
  const navigate = useNavigate()
  const [payment, setPayment] = useState<Payment | null>(null)
  const [charter, setCharter] = useState<Charter | null>(null)
  const [entity, setEntity] = useState<Entity | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [editForm, setEditForm] = useState<any>({})

  useEffect(() => {
    fetchPaymentDetails()
  }, [type, id])

  const fetchPaymentDetails = async () => {
    try {
      setLoading(true)
      const endpoint = type === 'vendor' 
        ? `/api/v1/charters/vendor-payments/${id}`
        : `/api/v1/charters/client-payments/${id}`
      
      const paymentResponse = await api.get(endpoint)
      setPayment(paymentResponse.data)

      // Fetch charter details
      const charterResponse = await api.get(`/api/v1/charters/${paymentResponse.data.charter_id}`)
      setCharter(charterResponse.data)

      // Fetch entity (vendor or client) details
      if (type === 'vendor' && paymentResponse.data.vendor_id) {
        const vendorResponse = await api.get(`/api/v1/auth/users/${paymentResponse.data.vendor_id}`)
        setEntity(vendorResponse.data)
      } else if (type === 'client' && paymentResponse.data.client_id) {
        const clientResponse = await api.get(`/api/v1/clients/${paymentResponse.data.client_id}`)
        setEntity(clientResponse.data)
      }
    } catch (err: any) {
      setError('Failed to load payment details')
      console.error('Error loading payment details:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleOpenEditDialog = () => {
    setEditForm({
      amount: payment?.amount,
      payment_date: payment?.payment_date || '',
      payment_method: payment?.payment_method || '',
      payment_status: payment?.payment_status,
      payment_type: payment?.payment_type || '',
      reference_number: payment?.reference_number || '',
      notes: payment?.notes || '',
    })
    setEditDialogOpen(true)
  }

  const handleSaveEdit = async () => {
    if (!payment) return

    try {
      const endpoint = type === 'vendor'
        ? `/api/v1/charters/vendor-payments/${id}`
        : `/api/v1/charters/client-payments/${id}`

      const updateData = {
        amount: parseFloat(editForm.amount),
        payment_date: editForm.payment_date || null,
        payment_method: editForm.payment_method || null,
        payment_status: editForm.payment_status,
        ...(type === 'client' && { payment_type: editForm.payment_type || null }),
        reference_number: editForm.reference_number || null,
        notes: editForm.notes || null,
      }

      await api.put(endpoint, updateData)
      setEditDialogOpen(false)
      fetchPaymentDetails()
    } catch (err: any) {
      console.error('Error updating payment:', err)
      setError('Failed to update payment')
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
    if (!method) return 'Not Specified'
    return method.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')
  }

  const getEntityName = (): string => {
    if (!entity) return 'Unknown'
    if (type === 'client') {
      return entity.company_name || `${entity.first_name || ''} ${entity.last_name || ''}`.trim()
    }
    return entity.name || entity.email || 'Unknown Vendor'
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  if (!payment) {
    return (
      <Alert severity="error">Payment not found</Alert>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <Button
            startIcon={<ArrowBack />}
            onClick={() => navigate('/payments')}
          >
            Back to Payments
          </Button>
          <Typography variant="h4" component="h1">
            Payment #{payment.id}
          </Typography>
          <Chip 
            label={type === 'client' ? 'Client Payment' : 'Vendor Payment'} 
            color={type === 'client' ? 'success' : 'warning'}
          />
        </Box>
        <Button
          variant="contained"
          startIcon={<Edit />}
          onClick={handleOpenEditDialog}
        >
          Edit Payment
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Payment Information */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <PaymentIcon sx={{ mr: 1 }} color="primary" />
                <Typography variant="h6">Payment Information</Typography>
              </Box>
              <Divider sx={{ mb: 2 }} />
              
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">Amount</Typography>
                  <Typography variant="h5" color={type === 'client' ? 'success.main' : 'error.main'}>
                    ${payment.amount.toFixed(2)}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">Status</Typography>
                  <Box mt={0.5}>
                    <Chip 
                      label={payment.payment_status} 
                      color={getPaymentStatusColor(payment.payment_status)}
                      size="small"
                    />
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">Payment Date</Typography>
                  <Typography variant="body1">
                    {payment.payment_date 
                      ? new Date(payment.payment_date).toLocaleDateString() 
                      : 'Not Set'
                    }
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">Payment Method</Typography>
                  <Typography variant="body1">
                    {getPaymentMethodLabel(payment.payment_method)}
                  </Typography>
                </Grid>
                {type === 'client' && payment.payment_type && (
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">Payment Type</Typography>
                    <Typography variant="body1">
                      {getPaymentMethodLabel(payment.payment_type)}
                    </Typography>
                  </Grid>
                )}
                <Grid item xs={payment.payment_type ? 6 : 12}>
                  <Typography variant="caption" color="text.secondary">Reference Number</Typography>
                  <Typography variant="body1">
                    {payment.reference_number || 'N/A'}
                  </Typography>
                </Grid>
                {payment.notes && (
                  <Grid item xs={12}>
                    <Typography variant="caption" color="text.secondary">Notes</Typography>
                    <Typography variant="body2" sx={{ mt: 0.5, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                      {payment.notes}
                    </Typography>
                  </Grid>
                )}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Entity Information */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                {type === 'client' ? <Business sx={{ mr: 1 }} color="primary" /> : <Person sx={{ mr: 1 }} color="primary" />}
                <Typography variant="h6">{type === 'client' ? 'Client' : 'Vendor'} Information</Typography>
              </Box>
              <Divider sx={{ mb: 2 }} />
              
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <Typography variant="caption" color="text.secondary">Name</Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {getEntityName()}
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="caption" color="text.secondary">Email</Typography>
                  <Typography variant="body1">
                    {entity?.email || 'N/A'}
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => navigate(type === 'client' ? `/clients/${payment.client_id}` : `/vendors/${payment.vendor_id}`)}
                  >
                    View {type === 'client' ? 'Client' : 'Vendor'} Profile
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Charter Information */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Receipt sx={{ mr: 1 }} color="primary" />
                <Typography variant="h6">Related Charter</Typography>
              </Box>
              <Divider sx={{ mb: 2 }} />
              
              {charter ? (
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={3}>
                    <Typography variant="caption" color="text.secondary">Charter ID</Typography>
                    <Typography variant="body1">#{charter.id}</Typography>
                  </Grid>
                  <Grid item xs={12} sm={3}>
                    <Typography variant="caption" color="text.secondary">Trip Date</Typography>
                    <Typography variant="body1">
                      {new Date(charter.trip_date).toLocaleDateString()}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={3}>
                    <Typography variant="caption" color="text.secondary">Status</Typography>
                    <Box mt={0.5}>
                      <Chip label={charter.status} size="small" color="primary" variant="outlined" />
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={3}>
                    <Typography variant="caption" color="text.secondary">Passengers</Typography>
                    <Typography variant="body1">{charter.passengers}</Typography>
                  </Grid>
                  {charter.pickup_location && (
                    <Grid item xs={12} sm={6}>
                      <Typography variant="caption" color="text.secondary">Pickup</Typography>
                      <Typography variant="body2">{charter.pickup_location}</Typography>
                    </Grid>
                  )}
                  {charter.dropoff_location && (
                    <Grid item xs={12} sm={6}>
                      <Typography variant="caption" color="text.secondary">Dropoff</Typography>
                      <Typography variant="body2">{charter.dropoff_location}</Typography>
                    </Grid>
                  )}
                  <Grid item xs={12} sm={4}>
                    <Typography variant="caption" color="text.secondary">
                      {type === 'vendor' ? 'Vendor Cost' : 'Client Charge'}
                    </Typography>
                    <Typography variant="h6" color={type === 'client' ? 'success.main' : 'error.main'}>
                      ${type === 'vendor' 
                        ? (charter.vendor_total_cost || 0).toFixed(2)
                        : (charter.client_total_charge || charter.total_cost).toFixed(2)
                      }
                    </Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <Button
                      variant="outlined"
                      onClick={() => navigate(`/charters/${charter.id}`)}
                    >
                      View Full Charter Details
                    </Button>
                  </Grid>
                </Grid>
              ) : (
                <Typography color="text.secondary">Charter information not available</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Metadata */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" mb={2}>
                Metadata
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={4}>
                  <Typography variant="caption" color="text.secondary">Created At</Typography>
                  <Typography variant="body2">
                    {new Date(payment.created_at).toLocaleString()}
                  </Typography>
                </Grid>
                {payment.updated_at && (
                  <Grid item xs={12} sm={4}>
                    <Typography variant="caption" color="text.secondary">Last Updated</Typography>
                    <Typography variant="body2">
                      {new Date(payment.updated_at).toLocaleString()}
                    </Typography>
                  </Grid>
                )}
                {payment.created_by && (
                  <Grid item xs={12} sm={4}>
                    <Typography variant="caption" color="text.secondary">Created By</Typography>
                    <Typography variant="body2">User #{payment.created_by}</Typography>
                  </Grid>
                )}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Payment</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Amount"
                type="number"
                value={editForm.amount || ''}
                onChange={(e) => setEditForm({ ...editForm, amount: e.target.value })}
                InputProps={{ startAdornment: '$' }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Payment Date"
                type="date"
                value={editForm.payment_date || ''}
                onChange={(e) => setEditForm({ ...editForm, payment_date: e.target.value })}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Payment Method</InputLabel>
                <Select
                  value={editForm.payment_method || ''}
                  label="Payment Method"
                  onChange={(e) => setEditForm({ ...editForm, payment_method: e.target.value })}
                >
                  <MenuItem value="">None</MenuItem>
                  <MenuItem value="check">Check</MenuItem>
                  <MenuItem value="wire_transfer">Wire Transfer</MenuItem>
                  <MenuItem value="ach">ACH</MenuItem>
                  <MenuItem value="credit_card">Credit Card</MenuItem>
                  <MenuItem value="cash">Cash</MenuItem>
                  {type === 'client' && <MenuItem value="invoice">Invoice</MenuItem>}
                  <MenuItem value="other">Other</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Payment Status</InputLabel>
                <Select
                  value={editForm.payment_status || 'pending'}
                  label="Payment Status"
                  onChange={(e) => setEditForm({ ...editForm, payment_status: e.target.value })}
                >
                  <MenuItem value="pending">Pending</MenuItem>
                  <MenuItem value="paid">Paid</MenuItem>
                  <MenuItem value="partial">Partial</MenuItem>
                  <MenuItem value="cancelled">Cancelled</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            {type === 'client' && (
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Payment Type</InputLabel>
                  <Select
                    value={editForm.payment_type || ''}
                    label="Payment Type"
                    onChange={(e) => setEditForm({ ...editForm, payment_type: e.target.value })}
                  >
                    <MenuItem value="">None</MenuItem>
                    <MenuItem value="deposit">Deposit</MenuItem>
                    <MenuItem value="partial_payment">Partial Payment</MenuItem>
                    <MenuItem value="full_payment">Full Payment</MenuItem>
                    <MenuItem value="final_payment">Final Payment</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            )}
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Reference Number"
                value={editForm.reference_number || ''}
                onChange={(e) => setEditForm({ ...editForm, reference_number: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Notes"
                multiline
                rows={3}
                value={editForm.notes || ''}
                onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveEdit} variant="contained">Save Changes</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
