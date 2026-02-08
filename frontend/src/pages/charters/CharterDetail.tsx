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
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Checkbox,
  FormControlLabel
} from '@mui/material'
import { 
  ArrowBack as BackIcon, 
  Delete as DeleteIcon, 
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  Add as AddIcon,
  ArrowUpward as ArrowUpIcon,
  ArrowDownward as ArrowDownIcon,
  Close as CloseIcon,
  Email as EmailIcon,
  Check as CheckIcon,
  CloudUpload as UploadIcon,
  Download as DownloadIcon,
  InsertDriveFile as FileIcon,
  ContentCopy as CopyIcon,
  Repeat as RepeatIcon,
  BookmarkAdd as TemplateIcon
} from '@mui/icons-material'
import api from '../../services/api'
import { useAuthStore } from '../../store/authStore'
import DocumentUploadDialog from '../../components/DocumentUploadDialog'
import { CloneCharterDialog } from '../../features/charter-templates/components/CloneCharterDialog'
import { RecurringCharterDialog } from '../../features/charter-templates/components/RecurringCharterDialog'
import { SaveAsTemplateDialog } from '../../features/charter-templates/components/SaveAsTemplateDialog'

interface Vehicle {
  id: number
  name: string
  capacity: number
  base_rate: number
  per_mile_rate: number
  is_active: boolean
}

interface Vendor {
  id: number
  email: string
  full_name: string
  role: string
}

interface Stop {
  id: number
  charter_id: number
  sequence: number
  location: string
  arrival_time: string | null
  departure_time: string | null
  notes: string | null
  created_at: string
}

interface Document {
  id: number
  charter_id: number
  document_type: string
  file_name: string
  file_size: number
  mime_type: string
  mongodb_id: string
  description: string | null
  uploaded_at: string
  uploaded_by: number | null
  download_url: string
}

interface Charter {
  id: number
  client_id: number
  vehicle_id: number
  vendor_id: number | null
  vendor_name: string | null
  vendor_email: string | null
  driver_id: number | null
  driver_name: string | null
  driver_email: string | null
  trip_date: string
  passengers: number
  trip_hours: number
  is_overnight: boolean
  is_weekend: boolean
  notes: string | null
  last_checkin_location: string | null
  last_checkin_time: string | null
  status: string
  // Legacy pricing
  base_cost: number
  mileage_cost: number
  additional_fees: number
  total_cost: number
  deposit_amount: number | null
  // Vendor pricing (what we pay to vendor)
  vendor_base_cost?: number | null
  vendor_mileage_cost?: number | null
  vendor_additional_fees?: number | null
  vendor_total_cost?: number | null
  // Client pricing (what we charge to client)
  client_base_charge?: number | null
  client_mileage_charge?: number | null
  client_additional_fees?: number | null
  client_total_charge?: number | null
  profit_margin?: number | null
  client_confirmation_name: string | null
  client_confirmation_email: string | null
  client_confirmation_date: string | null
  approval_sent_date: string | null
  quote_signed_date: string | null
  created_at: string
  updated_at: string | null
  vehicle: Vehicle
  stops: Stop[]
}

export default function CharterDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const currentUser = useAuthStore(state => state.user)
  const [charter, setCharter] = useState<Charter | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const [saving, setSaving] = useState(false)
  const [editedCharter, setEditedCharter] = useState<Partial<Charter>>({})
  const [editedStops, setEditedStops] = useState<Stop[]>([])
  const [vendors, setVendors] = useState<Vendor[]>([])
  const [drivers, setDrivers] = useState<Vendor[]>([])
  const [documents, setDocuments] = useState<Document[]>([])
  const [approvalDialogOpen, setApprovalDialogOpen] = useState(false)
  const [bookingDialogOpen, setBookingDialogOpen] = useState(false)
  const [confirmationDialogOpen, setConfirmationDialogOpen] = useState(false)
  const [executedApprovalDialogOpen, setExecutedApprovalDialogOpen] = useState(false)
  const [approvalAmount, setApprovalAmount] = useState('')
  const [bookingCost, setBookingCost] = useState('')
  const [selectedVendorId, setSelectedVendorId] = useState<number | ''>('')
  
  // Template and cloning dialogs
  const [cloneDialogOpen, setCloneDialogOpen] = useState(false)
  const [recurringDialogOpen, setRecurringDialogOpen] = useState(false)
  const [templateDialogOpen, setTemplateDialogOpen] = useState(false)

  useEffect(() => {
    if (id) {
      fetchCharter()
      fetchVendors()
      fetchDrivers()
      fetchDocuments()
    }
  }, [id])

  const fetchCharter = async () => {
    try {
      setLoading(true)
      const response = await api.get(`/api/v1/charters/${id}`)
      setCharter(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load charter')
    } finally {
      setLoading(false)
    }
  }

  const fetchVendors = async () => {
    try {
      const response = await api.get('/api/v1/auth/users')
      // Filter only users with vendor role
      const vendorUsers = response.data.filter((user: Vendor) => user.role === 'vendor')
      setVendors(vendorUsers)
    } catch (err: any) {
      console.error('Failed to load vendors:', err)
    }
  }

  const fetchDrivers = async () => {
    try {
      const response = await api.get('/api/v1/auth/users')
      // Filter only users with driver role
      const driverUsers = response.data.filter((user: Vendor) => user.role === 'driver')
      setDrivers(driverUsers)
    } catch (err: any) {
      console.error('Failed to load drivers:', err)
    }
  }

  const fetchDocuments = async () => {
    try {
      const response = await api.get(`/api/v1/documents/charter/${id}`)
      setDocuments(response.data)
    } catch (err: any) {
      console.error('Failed to load documents:', err)
    }
  }

  const handleDownloadDocument = async (documentId: number, fileName: string) => {
    try {
      const response = await api.get(`/api/v1/documents/${documentId}/download`, {
        responseType: 'blob'
      })
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', fileName)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      setError('Failed to download document')
    }
  }

  const handleDeleteDocument = async (documentId: number) => {
    if (!window.confirm('Are you sure you want to delete this document?')) {
      return
    }
    
    try {
      await api.delete(`/api/v1/documents/${documentId}`)
      fetchDocuments() // Refresh list
    } catch (err: any) {
      setError('Failed to delete document')
    }
  }

  const handleDelete = async () => {
    try {
      setDeleting(true)
      await api.delete(`/api/v1/charters/${id}`)
      navigate('/charters')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete charter')
    } finally {
      setDeleting(false)
      setDeleteDialogOpen(false)
    }
  }

  const handleSendApproval = async () => {
    // Open dialog instead of sending directly
    setApprovalDialogOpen(true)
  }

  const handleApprovalUploadComplete = async () => {
    if (!charter) return
    
    try {
      // Try to send approval email via notification service (optional)
      try {
        await api.post('/api/v1/notifications/notifications', {
          recipient_email: charter.client_confirmation_email || 'client@example.com',
          notification_type: 'email',
          template_name: 'quote_approval_request',
          charter_id: charter.id,
          template_data: {
            client_name: charter.client_confirmation_name || 'Valued Customer',
            trip_date: new Date(charter.trip_date).toLocaleDateString(),
            passengers: charter.passengers,
            vehicle_name: charter.vehicle.name,
            total_cost: `$${charter.total_cost.toFixed(2)}`,
            approval_link: `${window.location.origin}/charters/${charter.id}/approve`,
            quote_expiry_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toLocaleDateString()
          }
        })
      } catch (notificationErr) {
        console.warn('Notification service unavailable:', notificationErr)
        // Continue anyway - notification is optional
      }
      
      // Update charter with approval data
      const updates: any = {
        approval_sent_date: new Date().toISOString()
      }
      
      if (approvalAmount) {
        updates.approval_amount = parseFloat(approvalAmount)
        updates.approval_status = 'pending'
      }
      
      await api.put(`/api/v1/charters/${id}`, updates)
      
      fetchCharter() // Refresh to show updated status
      fetchDocuments() // Refresh documents list
      setApprovalAmount('')
      alert('Approval request sent successfully!')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send approval')
    }
  }

  const handleVendorBooked = async () => {
    // Open booking dialog
    setBookingDialogOpen(true)
  }

  const handleBookingUploadComplete = async () => {
    if (!charter) return
    
    try {
      const updates: any = {
        status: 'booked',
        booking_status: 'confirmed',
        booked_at: new Date().toISOString()
      }
      
      if (bookingCost) {
        updates.booking_cost = parseFloat(bookingCost)
      }
      
      if (selectedVendorId) {
        updates.vendor_id = selectedVendorId
      }
      
      await api.put(`/api/v1/charters/${id}`, updates)
      
      fetchCharter()
      fetchDocuments()
      setBookingCost('')
      setSelectedVendorId('')
      alert('Vendor booked! Charter status updated to Booked.')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to record booking')
    }
  }

  const handleSendConfirmation = async () => {
    // Open confirmation dialog
    setConfirmationDialogOpen(true)
  }

  const handleConfirmationUploadComplete = async () => {
    if (!charter) return
    
    try {
      // Update charter status to confirmed
      await api.put(`/api/v1/charters/${id}`, {
        status: 'confirmed',
        confirmation_status: 'sent',
        confirmed_at: new Date().toISOString()
      })
      
      fetchCharter()
      fetchDocuments()
      alert('Confirmation sent! Charter status updated to Confirmed.')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send confirmation')
    }
  }

  const handleExecutedApprovalUploadComplete = async () => {
    if (!charter) return
    
    try {
      // Update charter status to approved and set approval status
      await api.put(`/api/v1/charters/${id}`, {
        status: 'approved',
        approval_status: 'approved',
        quote_signed_date: new Date().toISOString()
      })
      
      fetchCharter()
      fetchDocuments()
      alert('Approval confirmed! Charter status updated to Approved.')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to confirm approval')
    }
  }

  const handleCheckIn = async () => {
    const location = prompt('Enter check-in location:')
    if (!location) return

    try {
      await api.post(`/api/v1/charters/${id}/checkin`, {
        location,
        checkin_time: new Date().toISOString()
      })
      await fetchCharter()
      setError('')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to record check-in')
    }
  }

  const handleEdit = () => {
    setEditMode(true)
    setEditedCharter({
      trip_date: charter?.trip_date,
      passengers: charter?.passengers,
      trip_hours: charter?.trip_hours,
      is_overnight: charter?.is_overnight,
      is_weekend: charter?.is_weekend,
      status: charter?.status,
      vendor_id: charter?.vendor_id,
      base_cost: charter?.base_cost,
      mileage_cost: charter?.mileage_cost,
      // Don't initialize additional_fees - let vendor/client specific fees be used
      // additional_fees: charter?.additional_fees,
      deposit_amount: charter?.deposit_amount,
      notes: charter?.notes
    })
    setEditedStops(charter?.stops ? [...charter.stops] : [])
  }

  const handleCancelEdit = () => {
    setEditMode(false)
    setEditedCharter({})
    setEditedStops([])
    setError('')
  }

  const handleSave = async () => {
    if (!charter) return
    
    try {
      setSaving(true)
      setError('')
      
      // Calculate totals
      const vendorTotalCost = (editedCharter.vendor_base_cost ?? charter.vendor_base_cost ?? charter.base_cost * 0.75) +
                              (editedCharter.vendor_mileage_cost ?? charter.vendor_mileage_cost ?? charter.mileage_cost * 0.75) +
                              (editedCharter.vendor_additional_fees ?? charter.vendor_additional_fees ?? 0)
      
      const clientTotalCharge = (editedCharter.client_base_charge ?? charter.client_base_charge ?? charter.base_cost) +
                                (editedCharter.client_mileage_charge ?? charter.client_mileage_charge ?? charter.mileage_cost) +
                                (editedCharter.client_additional_fees ?? charter.client_additional_fees ?? charter.additional_fees)
      
      const profitMargin = clientTotalCharge > 0 ? (clientTotalCharge - vendorTotalCost) / clientTotalCharge : 0
      
      // Legacy total_cost for backward compatibility - only calculate if explicitly edited
      const totalCost = (editedCharter.base_cost ?? charter.base_cost) + 
                        (editedCharter.mileage_cost ?? charter.mileage_cost) + 
                        (editedCharter.additional_fees ?? charter.additional_fees ?? 0)
      
      // Build update data - only include fields that were explicitly edited
      const updateData: any = {}
      
      // Copy all edited fields
      Object.keys(editedCharter).forEach(key => {
        updateData[key] = editedCharter[key as keyof typeof editedCharter]
      })
      
      // Always include calculated totals
      updateData.total_cost = totalCost
      updateData.vendor_total_cost = vendorTotalCost
      updateData.client_total_charge = clientTotalCharge
      updateData.profit_margin = profitMargin
      
      await api.put(`/api/v1/charters/${id}`, updateData)
      
      // Delete removed stops (original stops not in editedStops)
      const originalStopIds = charter?.stops?.map(s => s.id) || []
      const editedStopIds = editedStops.filter(s => s.id > 0).map(s => s.id)
      const deletedStopIds = originalStopIds.filter(id => !editedStopIds.includes(id))
      
      for (const stopId of deletedStopIds) {
        try {
          await api.delete(`/api/v1/charters/stops/${stopId}`)
        } catch (err) {
          console.error(`Failed to delete stop ${stopId}`, err)
        }
      }
      
      // Update or create stops
      for (const stop of editedStops) {
        const stopData = {
          location: stop.location,
          notes: stop.notes,
          sequence: stop.sequence,
          arrival_time: stop.arrival_time,
          departure_time: stop.departure_time
        }
        
        if (stop.id > 0) {
          // Update existing stop
          try {
            await api.put(`/api/v1/charters/stops/${stop.id}`, stopData)
          } catch (err) {
            console.error(`Failed to update stop ${stop.id}`, err)
          }
        } else {
          // Create new stop
          try {
            await api.post(`/api/v1/charters/${id}/stops`, stopData)
          } catch (err) {
            console.error('Failed to create stop', err)
          }
        }
      }
      
      await fetchCharter()
      setEditMode(false)
      setEditedCharter({})
      setEditedStops([])
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update charter')
    } finally {
      setSaving(false)
    }
  }

  const handleFieldChange = (field: keyof Charter, value: any) => {
    setEditedCharter(prev => ({ ...prev, [field]: value }))
  }

  const handleAddStop = () => {
    const newStop: Stop = {
      id: -Date.now(), // Temporary negative ID for new stops
      charter_id: charter?.id || 0,
      sequence: editedStops.length,
      location: '',
      arrival_time: null,
      departure_time: null,
      notes: null,
      created_at: new Date().toISOString()
    }
    setEditedStops([...editedStops, newStop])
  }

  const handleDeleteStop = (index: number) => {
    setEditedStops(editedStops.filter((_, i) => i !== index).map((stop, i) => ({
      ...stop,
      sequence: i
    })))
  }

  const handleMoveStopUp = (index: number) => {
    if (index === 0) return
    const newStops = [...editedStops]
    // Swap the stops
    const temp = newStops[index]
    newStops[index] = newStops[index - 1]
    newStops[index - 1] = temp
    // Update sequence numbers for all stops
    newStops.forEach((stop, i) => {
      stop.sequence = i
    })
    setEditedStops(newStops)
  }

  const handleMoveStopDown = (index: number) => {
    if (index === editedStops.length - 1) return
    const newStops = [...editedStops]
    // Swap the stops
    const temp = newStops[index]
    newStops[index] = newStops[index + 1]
    newStops[index + 1] = temp
    // Update sequence numbers for all stops
    newStops.forEach((stop, i) => {
      stop.sequence = i
    })
    setEditedStops(newStops)
  }

  const handleStopChange = (index: number, field: keyof Stop, value: any) => {
    setEditedStops(editedStops.map((stop, i) => 
      i === index ? { ...stop, [field]: value } : stop
    ))
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'quote': return 'info'
      case 'approved': return 'primary'
      case 'booked': return 'secondary'
      case 'confirmed': return 'success'
      case 'in_progress': return 'warning'
      case 'completed': return 'success'
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
        <Button onClick={() => navigate('/charters')} sx={{ mt: 2 }}>
          Back to Charters
        </Button>
      </Box>
    )
  }

  if (!charter) {
    return (
      <Box>
        <Alert severity="warning">Charter not found</Alert>
        <Button onClick={() => navigate('/charters')} sx={{ mt: 2 }}>
          Back to Charters
        </Button>
      </Box>
    )
  }

  return (
    <Box>
      <Button
        startIcon={<BackIcon />}
        onClick={() => navigate('/charters')}
        sx={{ mb: 2 }}
      >
        Back to Charters
      </Button>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Charter #{charter.id}</Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Chip 
            label={editMode ? (editedCharter.status || charter.status) : charter.status} 
            color={getStatusColor(editMode ? (editedCharter.status || charter.status) : charter.status)} 
          />
          {!editMode ? (
            <>
              {charter.status === 'quote' && (
                <>
                  <Button
                    variant="contained"
                    color="success"
                    startIcon={<EmailIcon />}
                    onClick={handleSendApproval}
                  >
                    Send for Approval
                  </Button>
                  <Button
                    variant="contained"
                    color="primary"
                    startIcon={<CheckIcon />}
                    onClick={() => setExecutedApprovalDialogOpen(true)}
                  >
                    Confirm Approval
                  </Button>
                </>
              )}
              {charter.status === 'approved' && (
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<UploadIcon />}
                  onClick={handleVendorBooked}
                >
                  Vendor Booked
                </Button>
              )}
              {charter.status === 'booked' && (
                <Button
                  variant="contained"
                  color="info"
                  startIcon={<EmailIcon />}
                  onClick={handleSendConfirmation}
                >
                  Send Confirmation
                </Button>
              )}
              <Button
                variant="contained"
                color="primary"
                onClick={handleCheckIn}
                disabled={charter.status === 'cancelled'}
              >
                Check In
              </Button>
              <Button
                variant="outlined"
                startIcon={<EditIcon />}
                onClick={handleEdit}
              >
                Edit
              </Button>
              <Button
                variant="outlined"
                startIcon={<CopyIcon />}
                onClick={() => setCloneDialogOpen(true)}
              >
                Clone
              </Button>
              <Button
                variant="outlined"
                startIcon={<RepeatIcon />}
                onClick={() => setRecurringDialogOpen(true)}
              >
                Recurring
              </Button>
              <Button
                variant="outlined"
                startIcon={<TemplateIcon />}
                onClick={() => setTemplateDialogOpen(true)}
              >
                Save as Template
              </Button>
              {currentUser?.is_superuser && (
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<DeleteIcon />}
                  onClick={() => setDeleteDialogOpen(true)}
                >
                  Delete
                </Button>
              )}
            </>
          ) : (
            <>
              <Button
                variant="outlined"
                startIcon={<CancelIcon />}
                onClick={handleCancelEdit}
                disabled={saving}
              >
                Cancel
              </Button>
              <Button
                variant="contained"
                startIcon={<SaveIcon />}
                onClick={handleSave}
                disabled={saving}
              >
                {saving ? <CircularProgress size={20} /> : 'Save'}
              </Button>
            </>
          )}
        </Box>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Trip Information
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Trip Date</Typography>
              {editMode ? (
                <TextField
                  fullWidth
                  type="date"
                  size="small"
                  value={editedCharter.trip_date || charter.trip_date}
                  onChange={(e) => handleFieldChange('trip_date', e.target.value)}
                  sx={{ mt: 0.5 }}
                />
              ) : (
                <Typography variant="body1">
                  {new Date(charter.trip_date).toLocaleDateString()}
                </Typography>
              )}
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Passengers</Typography>
              {editMode ? (
                <TextField
                  fullWidth
                  type="number"
                  size="small"
                  value={editedCharter.passengers ?? charter.passengers}
                  onChange={(e) => handleFieldChange('passengers', parseInt(e.target.value) || 0)}
                  InputProps={{ inputProps: { min: 1 } }}
                  sx={{ mt: 0.5 }}
                />
              ) : (
                <Typography variant="body1">{charter.passengers}</Typography>
              )}
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Duration</Typography>
              {editMode ? (
                <TextField
                  fullWidth
                  type="number"
                  size="small"
                  value={editedCharter.trip_hours ?? charter.trip_hours}
                  onChange={(e) => handleFieldChange('trip_hours', parseFloat(e.target.value) || 0)}
                  InputProps={{ inputProps: { min: 0.5, step: 0.5 } }}
                  sx={{ mt: 0.5 }}
                />
              ) : (
                <Typography variant="body1">{charter.trip_hours} hours</Typography>
              )}
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Trip Type</Typography>
              {editMode ? (
                <Box sx={{ mt: 0.5 }}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={editedCharter.is_overnight ?? charter.is_overnight}
                        onChange={(e) => handleFieldChange('is_overnight', e.target.checked)}
                      />
                    }
                    label="Overnight"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={editedCharter.is_weekend ?? charter.is_weekend}
                        onChange={(e) => handleFieldChange('is_weekend', e.target.checked)}
                      />
                    }
                    label="Weekend"
                  />
                </Box>
              ) : (
                <Box sx={{ mt: 0.5 }}>
                  {charter.is_overnight && <Chip label="Overnight" size="small" sx={{ mr: 1 }} />}
                  {charter.is_weekend && <Chip label="Weekend" size="small" />}
                  {!charter.is_overnight && !charter.is_weekend && <Typography variant="body2">Standard</Typography>}
                </Box>
              )}
            </Box>

            {editMode && (
              <Box sx={{ mb: 2 }}>
                <FormControl fullWidth size="small">
                  <InputLabel>Status</InputLabel>
                  <Select
                    value={editedCharter.status || charter.status}
                    label="Status"
                    onChange={(e) => handleFieldChange('status', e.target.value)}
                  >
                    <MenuItem value="quote">Quote</MenuItem>
                    <MenuItem value="approved">Approved</MenuItem>
                    <MenuItem value="booked">Booked</MenuItem>
                    <MenuItem value="confirmed">Confirmed</MenuItem>
                    <MenuItem value="in_progress">In Progress</MenuItem>
                    <MenuItem value="completed">Completed</MenuItem>
                    <MenuItem value="cancelled">Cancelled</MenuItem>
                  </Select>
                </FormControl>
              </Box>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Vehicle Information
            </Typography>
            <Divider sx={{ mb: 2 }} />

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Vehicle</Typography>
              <Typography variant="body1">{charter.vehicle.name}</Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Capacity</Typography>
              <Typography variant="body1">{charter.vehicle.capacity} passengers</Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Base Rate</Typography>
              <Typography variant="body1">${charter.vehicle.base_rate.toFixed(2)}/hour</Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Mileage Rate</Typography>
              <Typography variant="body1">${charter.vehicle.per_mile_rate.toFixed(2)}/mile</Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Assigned Vendor</Typography>
              {editMode ? (
                <FormControl fullWidth size="small" sx={{ mt: 0.5 }}>
                  <InputLabel>Select Vendor</InputLabel>
                  <Select
                    value={editedCharter.vendor_id ?? charter.vendor_id ?? ''}
                    label="Select Vendor"
                    onChange={(e) => handleFieldChange('vendor_id', e.target.value || null)}
                  >
                    <MenuItem value="">
                      <em>Unassigned</em>
                    </MenuItem>
                    {vendors.map((vendor) => (
                      <MenuItem key={vendor.id} value={vendor.id}>
                        {vendor.full_name} ({vendor.email})
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              ) : charter.vendor_name ? (
                <Box>
                  <Typography variant="body1">{charter.vendor_name}</Typography>
                  <Typography variant="caption" color="textSecondary">{charter.vendor_email}</Typography>
                </Box>
              ) : (
                <Typography variant="body2" color="textSecondary">No vendor assigned</Typography>
              )}
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="textSecondary">Assigned Driver</Typography>
              {editMode ? (
                <FormControl fullWidth size="small" sx={{ mt: 0.5 }}>
                  <InputLabel>Select Driver</InputLabel>
                  <Select
                    value={editedCharter.driver_id ?? charter.driver_id ?? ''}
                    label="Select Driver"
                    onChange={(e) => handleFieldChange('driver_id', e.target.value || null)}
                  >
                    <MenuItem value="">
                      <em>Unassigned</em>
                    </MenuItem>
                    {drivers.map((driver) => (
                      <MenuItem key={driver.id} value={driver.id}>
                        {driver.full_name} ({driver.email})
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              ) : charter.driver_name ? (
                <Box>
                  <Typography variant="body1">{charter.driver_name}</Typography>
                  <Typography variant="caption" color="textSecondary">{charter.driver_email}</Typography>
                </Box>
              ) : (
                <Typography variant="body2" color="textSecondary">No driver assigned</Typography>
              )}
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Pricing Breakdown
            </Typography>
            <Divider sx={{ mb: 2 }} />

            {editMode ? (
              <Box>
                {/* Vendor Costs Section */}
                <Typography variant="subtitle1" color="error.main" gutterBottom sx={{ mt: 2 }}>
                  Vendor Costs (What We Pay)
                </Typography>
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  <Grid item xs={12} sm={6} md={3}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Vendor Base Cost"
                      size="small"
                      value={editedCharter.vendor_base_cost ?? charter.vendor_base_cost ?? charter.base_cost * 0.75}
                      onChange={(e) => handleFieldChange('vendor_base_cost', parseFloat(e.target.value) || 0)}
                      InputProps={{ inputProps: { min: 0, step: 0.01 } }}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Vendor Mileage Cost"
                      size="small"
                      value={editedCharter.vendor_mileage_cost ?? charter.vendor_mileage_cost ?? charter.mileage_cost * 0.75}
                      onChange={(e) => handleFieldChange('vendor_mileage_cost', parseFloat(e.target.value) || 0)}
                      InputProps={{ inputProps: { min: 0, step: 0.01 } }}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Vendor Additional Fees"
                      size="small"
                      value={editedCharter.vendor_additional_fees ?? charter.vendor_additional_fees ?? 0}
                      onChange={(e) => handleFieldChange('vendor_additional_fees', parseFloat(e.target.value) || 0)}
                      InputProps={{ inputProps: { min: 0, step: 0.01 } }}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Box>
                      <Typography variant="caption" color="textSecondary">Vendor Total Cost</Typography>
                      <Typography variant="h6" color="error.main">
                        ${((editedCharter.vendor_base_cost ?? charter.vendor_base_cost ?? charter.base_cost * 0.75) + 
                           (editedCharter.vendor_mileage_cost ?? charter.vendor_mileage_cost ?? charter.mileage_cost * 0.75) + 
                           (editedCharter.vendor_additional_fees ?? charter.vendor_additional_fees ?? 0)).toFixed(2)}
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>

                {/* Client Charges Section */}
                <Typography variant="subtitle1" color="success.main" gutterBottom sx={{ mt: 2 }}>
                  Client Charges (What We Charge)
                </Typography>
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  <Grid item xs={12} sm={6} md={3}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Client Base Charge"
                      size="small"
                      value={editedCharter.client_base_charge ?? charter.client_base_charge ?? charter.base_cost}
                      onChange={(e) => handleFieldChange('client_base_charge', parseFloat(e.target.value) || 0)}
                      InputProps={{ inputProps: { min: 0, step: 0.01 } }}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Client Mileage Charge"
                      size="small"
                      value={editedCharter.client_mileage_charge ?? charter.client_mileage_charge ?? charter.mileage_cost}
                      onChange={(e) => handleFieldChange('client_mileage_charge', parseFloat(e.target.value) || 0)}
                      InputProps={{ inputProps: { min: 0, step: 0.01 } }}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Client Additional Fees"
                      size="small"
                      value={editedCharter.client_additional_fees ?? charter.client_additional_fees ?? charter.additional_fees}
                      onChange={(e) => handleFieldChange('client_additional_fees', parseFloat(e.target.value) || 0)}
                      InputProps={{ inputProps: { min: 0, step: 0.01 } }}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Box>
                      <Typography variant="caption" color="textSecondary">Client Total Charge</Typography>
                      <Typography variant="h6" color="success.main">
                        ${((editedCharter.client_base_charge ?? charter.client_base_charge ?? charter.base_cost) + 
                           (editedCharter.client_mileage_charge ?? charter.client_mileage_charge ?? charter.mileage_cost) + 
                           (editedCharter.client_additional_fees ?? charter.client_additional_fees ?? charter.additional_fees)).toFixed(2)}
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>

                {/* Profit Summary */}
                <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="caption" color="textSecondary">Profit Amount</Typography>
                      <Typography variant="h6" color="info.dark">
                        ${(((editedCharter.client_base_charge ?? charter.client_base_charge ?? charter.base_cost) + 
                             (editedCharter.client_mileage_charge ?? charter.client_mileage_charge ?? charter.mileage_cost) + 
                             (editedCharter.client_additional_fees ?? charter.client_additional_fees ?? charter.additional_fees)) -
                            ((editedCharter.vendor_base_cost ?? charter.vendor_base_cost ?? charter.base_cost * 0.75) + 
                             (editedCharter.vendor_mileage_cost ?? charter.vendor_mileage_cost ?? charter.mileage_cost * 0.75) + 
                             (editedCharter.vendor_additional_fees ?? charter.vendor_additional_fees ?? 0))).toFixed(2)}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="caption" color="textSecondary">Profit Margin</Typography>
                      <Typography variant="h6" color="info.dark">
                        {(((((editedCharter.client_base_charge ?? charter.client_base_charge ?? charter.base_cost) + 
                              (editedCharter.client_mileage_charge ?? charter.client_mileage_charge ?? charter.mileage_cost) + 
                              (editedCharter.client_additional_fees ?? charter.client_additional_fees ?? charter.additional_fees)) -
                             ((editedCharter.vendor_base_cost ?? charter.vendor_base_cost ?? charter.base_cost * 0.75) + 
                              (editedCharter.vendor_mileage_cost ?? charter.vendor_mileage_cost ?? charter.mileage_cost * 0.75) + 
                              (editedCharter.vendor_additional_fees ?? charter.vendor_additional_fees ?? 0))) /
                            ((editedCharter.client_base_charge ?? charter.client_base_charge ?? charter.base_cost) + 
                             (editedCharter.client_mileage_charge ?? charter.client_mileage_charge ?? charter.mileage_cost) + 
                             (editedCharter.client_additional_fees ?? charter.client_additional_fees ?? charter.additional_fees))) * 100).toFixed(1)}%
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <TextField
                        fullWidth
                        type="number"
                        label="Deposit Amount"
                        size="small"
                        value={editedCharter.deposit_amount ?? charter.deposit_amount ?? ''}
                        onChange={(e) => handleFieldChange('deposit_amount', e.target.value ? parseFloat(e.target.value) : null)}
                        InputProps={{ inputProps: { min: 0, step: 0.01 } }}
                      />
                    </Grid>
                  </Grid>
                </Box>
              </Box>
            ) : (
              <Box>
                {/* Vendor Costs Display */}
                <Typography variant="subtitle1" color="error.main" gutterBottom>
                  Vendor Costs (What We Pay)
                </Typography>
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="textSecondary">Base Cost</Typography>
                    <Typography variant="h6">${(charter.vendor_base_cost ?? charter.base_cost * 0.75).toFixed(2)}</Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="textSecondary">Mileage Cost</Typography>
                    <Typography variant="h6">${(charter.vendor_mileage_cost ?? charter.mileage_cost * 0.75).toFixed(2)}</Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="textSecondary">Additional Fees</Typography>
                    <Typography variant="h6">${(charter.vendor_additional_fees ?? 0).toFixed(2)}</Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="textSecondary">Total Vendor Cost</Typography>
                    <Typography variant="h6" color="error.main">
                      ${((charter.vendor_base_cost ?? charter.base_cost * 0.75) + 
                          (charter.vendor_mileage_cost ?? charter.mileage_cost * 0.75) + 
                          (charter.vendor_additional_fees ?? charter.additional_fees ?? 0)).toFixed(2)}
                    </Typography>
                  </Grid>
                </Grid>

                <Divider sx={{ my: 2 }} />

                {/* Client Charges Display */}
                <Typography variant="subtitle1" color="success.main" gutterBottom>
                  Client Charges (What We Charge)
                </Typography>
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="textSecondary">Base Charge</Typography>
                    <Typography variant="h6">${(charter.client_base_charge ?? charter.base_cost).toFixed(2)}</Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="textSecondary">Mileage Charge</Typography>
                    <Typography variant="h6">${(charter.client_mileage_charge ?? charter.mileage_cost).toFixed(2)}</Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="textSecondary">Additional Fees</Typography>
                    <Typography variant="h6">${(charter.client_additional_fees ?? charter.additional_fees).toFixed(2)}</Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="textSecondary">Total Client Charge</Typography>
                    <Typography variant="h6" color="success.main">
                      ${((charter.client_base_charge ?? charter.base_cost) + 
                          (charter.client_mileage_charge ?? charter.mileage_cost) + 
                          (charter.client_additional_fees ?? charter.additional_fees ?? 0)).toFixed(2)}
                    </Typography>
                  </Grid>
                </Grid>

                <Divider sx={{ my: 2 }} />

                {/* Profit Summary Display */}
                <Box sx={{ p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="caption" color="textSecondary">Our Profit</Typography>
                      <Typography variant="h6" color="info.dark">
                        ${((((charter.client_base_charge ?? charter.base_cost) + 
                              (charter.client_mileage_charge ?? charter.mileage_cost) + 
                              (charter.client_additional_fees ?? charter.additional_fees ?? 0)) -
                             ((charter.vendor_base_cost ?? charter.base_cost * 0.75) + 
                              (charter.vendor_mileage_cost ?? charter.mileage_cost * 0.75) + 
                              (charter.vendor_additional_fees ?? charter.additional_fees ?? 0)))).toFixed(2)}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="caption" color="textSecondary">Profit Margin</Typography>
                      <Typography variant="h6" color="info.dark">
                        {(() => {
                          const clientTotal = (charter.client_base_charge ?? charter.base_cost) + 
                            (charter.client_mileage_charge ?? charter.mileage_cost) + 
                            (charter.client_additional_fees ?? charter.additional_fees ?? 0)
                          const vendorTotal = (charter.vendor_base_cost ?? charter.base_cost * 0.75) + 
                            (charter.vendor_mileage_cost ?? charter.mileage_cost * 0.75) + 
                            (charter.vendor_additional_fees ?? charter.additional_fees ?? 0)
                          const margin = clientTotal > 0 ? ((clientTotal - vendorTotal) / clientTotal * 100) : 0
                          return `${margin.toFixed(1)}%`
                        })()}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="caption" color="textSecondary">Deposit Required</Typography>
                      <Typography variant="h6">${charter.deposit_amount?.toFixed(2) ?? '0.00'}</Typography>
                    </Grid>
                  </Grid>
                </Box>
              </Box>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Client Confirmation
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <Typography variant="caption" color="textSecondary">Contact Name</Typography>
                {editMode ? (
                  <TextField
                    fullWidth
                    size="small"
                    value={editedCharter.client_confirmation_name || charter.client_confirmation_name || ''}
                    onChange={(e) => handleFieldChange('client_confirmation_name', e.target.value)}
                    placeholder="Enter client contact name"
                    sx={{ mt: 0.5 }}
                  />
                ) : (
                  <Typography variant="body1">{charter.client_confirmation_name || 'Not set'}</Typography>
                )}
              </Grid>
              
              <Grid item xs={12} md={4}>
                <Typography variant="caption" color="textSecondary">Contact Email</Typography>
                {editMode ? (
                  <TextField
                    fullWidth
                    size="small"
                    type="email"
                    value={editedCharter.client_confirmation_email || charter.client_confirmation_email || ''}
                    onChange={(e) => handleFieldChange('client_confirmation_email', e.target.value)}
                    placeholder="client@example.com"
                    sx={{ mt: 0.5 }}
                  />
                ) : (
                  <Typography variant="body1">{charter.client_confirmation_email || 'Not set'}</Typography>
                )}
              </Grid>
              
              <Grid item xs={12} md={4}>
                <Typography variant="caption" color="textSecondary">Confirmation Date</Typography>
                <Typography variant="body1">
                  {charter.client_confirmation_date 
                    ? new Date(charter.client_confirmation_date).toLocaleDateString()
                    : 'Not confirmed'}
                </Typography>
              </Grid>
              
              {charter.approval_sent_date && (
                <Grid item xs={12} md={4}>
                  <Typography variant="caption" color="textSecondary">Approval Sent</Typography>
                  <Typography variant="body1" color="success.main">
                    <CheckIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                    {new Date(charter.approval_sent_date).toLocaleDateString()}
                  </Typography>
                </Grid>
              )}
              
              {charter.quote_signed_date && (
                <Grid item xs={12} md={4}>
                  <Typography variant="caption" color="textSecondary">Quote Signed</Typography>
                  <Typography variant="body1" color="success.main">
                    <CheckIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                    {new Date(charter.quote_signed_date).toLocaleDateString()}
                  </Typography>
                </Grid>
              )}
            </Grid>
          </Paper>
        </Grid>

        {((charter.stops && charter.stops.length > 0) || editMode) && (
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Trip Itinerary ({editMode ? editedStops.length : charter.stops.length} stops)
                </Typography>
                {editMode && (
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<AddIcon />}
                    onClick={handleAddStop}
                  >
                    Add Stop
                  </Button>
                )}
              </Box>
              <Divider sx={{ mb: 2 }} />
              
              {editMode ? (
                <Box>
                  {editedStops.length === 0 ? (
                    <Alert severity="info">No stops added yet. Click "Add Stop" to create the itinerary.</Alert>
                  ) : (
                    editedStops.map((stop, index) => (
                      <Paper key={stop.id} variant="outlined" sx={{ p: 2, mb: 2 }}>
                        <Grid container spacing={2} alignItems="center">
                          <Grid item xs={12} sm={1}>
                            <Typography variant="body2" fontWeight="bold">
                              Stop {index + 1}
                            </Typography>
                          </Grid>
                          <Grid item xs={12} sm={5}>
                            <TextField
                              fullWidth
                              size="small"
                              label="Location"
                              value={stop.location}
                              onChange={(e) => handleStopChange(index, 'location', e.target.value)}
                              placeholder="123 Main St, City, State"
                            />
                          </Grid>
                          <Grid item xs={12} sm={3}>
                            <TextField
                              fullWidth
                              size="small"
                              label="Arrival Time"
                              type="time"
                              value={stop.arrival_time ? new Date(stop.arrival_time).toTimeString().slice(0, 5) : ''}
                              onChange={(e) => {
                                const tripDate = charter.trip_date || new Date().toISOString().split('T')[0]
                                const dateTimeStr = e.target.value ? `${tripDate}T${e.target.value}:00` : null
                                handleStopChange(index, 'arrival_time', dateTimeStr)
                              }}
                              InputLabelProps={{ shrink: true }}
                            />
                          </Grid>
                          <Grid item xs={12} sm={3}>
                            <TextField
                              fullWidth
                              size="small"
                              label="Departure Time"
                              type="time"
                              value={stop.departure_time ? new Date(stop.departure_time).toTimeString().slice(0, 5) : ''}
                              onChange={(e) => {
                                const tripDate = charter.trip_date || new Date().toISOString().split('T')[0]
                                const dateTimeStr = e.target.value ? `${tripDate}T${e.target.value}:00` : null
                                handleStopChange(index, 'departure_time', dateTimeStr)
                              }}
                              InputLabelProps={{ shrink: true }}
                            />
                          </Grid>
                          <Grid item xs={12}>
                            <TextField
                              fullWidth
                              size="small"
                              label="Notes"
                              value={stop.notes || ''}
                              onChange={(e) => handleStopChange(index, 'notes', e.target.value)}
                              placeholder="Pickup/dropoff instructions"
                            />
                          </Grid>
                          <Grid item xs={12}>
                            <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'flex-end' }}>
                              <Button
                                size="small"
                                onClick={() => handleMoveStopUp(index)}
                                disabled={index === 0}
                              >
                                <ArrowUpIcon fontSize="small" />
                              </Button>
                              <Button
                                size="small"
                                onClick={() => handleMoveStopDown(index)}
                                disabled={index === editedStops.length - 1}
                              >
                                <ArrowDownIcon fontSize="small" />
                              </Button>
                              <Button
                                size="small"
                                color="error"
                                onClick={() => handleDeleteStop(index)}
                              >
                                <CloseIcon fontSize="small" />
                              </Button>
                            </Box>
                          </Grid>
                        </Grid>
                      </Paper>
                    ))
                  )}
                </Box>
              ) : (
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Stop #</TableCell>
                        <TableCell>Location</TableCell>
                        <TableCell>Arrival Time</TableCell>
                        <TableCell>Departure Time</TableCell>
                        <TableCell>Notes</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {(charter.stops || [])
                        .sort((a, b) => a.sequence - b.sequence)
                        .map((stop) => (
                          <TableRow key={stop.id}>
                            <TableCell>{stop.sequence}</TableCell>
                            <TableCell>{stop.location}</TableCell>
                            <TableCell>
                              {stop.arrival_time ? new Date(stop.arrival_time).toLocaleTimeString('en-US', {
                                hour: '2-digit',
                                minute: '2-digit'
                              }) : '-'}
                            </TableCell>
                            <TableCell>
                              {stop.departure_time ? new Date(stop.departure_time).toLocaleTimeString('en-US', {
                                hour: '2-digit',
                                minute: '2-digit'
                              }) : '-'}
                            </TableCell>
                            <TableCell>{stop.notes || '-'}</TableCell>
                          </TableRow>
                        ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </Paper>
          </Grid>
        )}

        {(charter.notes || editMode) && (
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Special Requirements / Notes
              </Typography>
              <Divider sx={{ mb: 2 }} />
              {editMode ? (
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  value={editedCharter.notes ?? charter.notes ?? ''}
                  onChange={(e) => handleFieldChange('notes', e.target.value)}
                  placeholder="Add special requirements or notes..."
                />
              ) : (
                <Typography variant="body1">{charter.notes}</Typography>
              )}
            </Paper>
          </Grid>
        )}

        {(charter.last_checkin_location || editMode) && (
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Last Check-in Location
              </Typography>
              <Divider sx={{ mb: 2 }} />
              {editMode ? (
                <TextField
                  fullWidth
                  value={editedCharter.last_checkin_location ?? charter.last_checkin_location ?? ''}
                  onChange={(e) => handleFieldChange('last_checkin_location', e.target.value)}
                  placeholder="Enter last check-in location..."
                />
              ) : (
                <>
                  <Typography variant="body1">{charter.last_checkin_location}</Typography>
                  {charter.last_checkin_time && (
                    <Typography variant="caption" color="textSecondary" display="block" sx={{ mt: 1 }}>
                      Checked in at: {new Date(charter.last_checkin_time).toLocaleString()}
                    </Typography>
                  )}
                </>
              )}
            </Paper>
          </Grid>
        )}

        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Metadata
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Typography variant="caption" color="textSecondary">Created</Typography>
                <Typography variant="body2">
                  {new Date(charter.created_at).toLocaleString()}
                </Typography>
              </Grid>
              {charter.updated_at && (
                <Grid item xs={12} sm={6}>
                  <Typography variant="caption" color="textSecondary">Last Updated</Typography>
                  <Typography variant="body2">
                    {new Date(charter.updated_at).toLocaleString()}
                  </Typography>
                </Grid>
              )}
            </Grid>
          </Paper>
        </Grid>

        {/* Documents Section */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Documents
              </Typography>
              <Chip label={`${documents.length} files`} size="small" color="primary" />
            </Box>
            <Divider sx={{ mb: 2 }} />
            
            {documents.length === 0 ? (
              <Typography variant="body2" color="textSecondary" align="center" sx={{ py: 3 }}>
                No documents uploaded yet
              </Typography>
            ) : (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>File Name</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Size</TableCell>
                      <TableCell>Uploaded</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {documents.map((doc) => (
                      <TableRow key={doc.id}>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <FileIcon fontSize="small" color="action" />
                            {doc.file_name}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={doc.document_type} 
                            size="small" 
                            color={
                              doc.document_type === 'approval' ? 'success' :
                              doc.document_type === 'booking' ? 'primary' :
                              doc.document_type === 'confirmation' ? 'info' :
                              'default'
                            }
                          />
                        </TableCell>
                        <TableCell>{(doc.file_size / 1024).toFixed(2)} KB</TableCell>
                        <TableCell>{new Date(doc.uploaded_at).toLocaleDateString()}</TableCell>
                        <TableCell align="right">
                          <Button
                            size="small"
                            startIcon={<DownloadIcon />}
                            onClick={() => handleDownloadDocument(doc.id, doc.file_name)}
                          >
                            Download
                          </Button>
                          {currentUser?.is_superuser && (
                            <Button
                              size="small"
                              color="error"
                              startIcon={<DeleteIcon />}
                              onClick={() => handleDeleteDocument(doc.id)}
                            >
                              Delete
                            </Button>
                          )}
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

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => !deleting && setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete Charter</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete Charter #{charter.id}? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)} disabled={deleting}>
            Cancel
          </Button>
          <Button onClick={handleDelete} color="error" disabled={deleting}>
            {deleting ? <CircularProgress size={24} /> : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Document Upload Dialogs */}
      <DocumentUploadDialog
        open={approvalDialogOpen}
        onClose={() => setApprovalDialogOpen(false)}
        onUploadComplete={handleApprovalUploadComplete}
        charterId={charter.id}
        documentType="approval"
        title="Upload Approval Document"
        additionalFields={
          <TextField
            fullWidth
            label="Approval Amount"
            type="number"
            value={approvalAmount}
            onChange={(e) => setApprovalAmount(e.target.value)}
            InputProps={{ inputProps: { min: 0, step: 0.01 } }}
            sx={{ mb: 2 }}
          />
        }
      />

      <DocumentUploadDialog
        open={bookingDialogOpen}
        onClose={() => setBookingDialogOpen(false)}
        onUploadComplete={handleBookingUploadComplete}
        charterId={charter.id}
        documentType="booking"
        title="Upload Vendor Booking Document"
        additionalFields={
          <>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Select Vendor</InputLabel>
              <Select
                value={selectedVendorId}
                onChange={(e) => setSelectedVendorId(e.target.value as number)}
                label="Select Vendor"
              >
                <MenuItem value="">
                  <em>None</em>
                </MenuItem>
                {vendors.map((vendor) => (
                  <MenuItem key={vendor.id} value={vendor.id}>
                    {vendor.full_name} ({vendor.email})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="Booking Cost"
              type="number"
              value={bookingCost}
              onChange={(e) => setBookingCost(e.target.value)}
              InputProps={{ inputProps: { min: 0, step: 0.01 } }}
              sx={{ mb: 2 }}
            />
          </>
        }
      />

      <DocumentUploadDialog
        open={confirmationDialogOpen}
        onClose={() => setConfirmationDialogOpen(false)}
        onUploadComplete={handleConfirmationUploadComplete}
        charterId={charter.id}
        documentType="confirmation"
        title="Upload Confirmation Document"
      />

      <DocumentUploadDialog
        open={executedApprovalDialogOpen}
        onClose={() => setExecutedApprovalDialogOpen(false)}
        onUploadComplete={handleExecutedApprovalUploadComplete}
        charterId={charter.id}
        documentType="approval"
        title="Upload Executed Approval Document"
      />

      {/* Clone and Template Dialogs */}
      {charter && (
        <>
          <CloneCharterDialog
            open={cloneDialogOpen}
            onClose={() => setCloneDialogOpen(false)}
            charterId={charter.id}
            currentTripDate={charter.trip_date}
          />

          <RecurringCharterDialog
            open={recurringDialogOpen}
            onClose={() => setRecurringDialogOpen(false)}
            charterId={charter.id}
            clientId={charter.client_id}
            currentTripDate={charter.trip_date}
          />

          <SaveAsTemplateDialog
            open={templateDialogOpen}
            onClose={() => setTemplateDialogOpen(false)}
            charterId={charter.id}
          />
        </>
      )}
    </Box>
  )
}
