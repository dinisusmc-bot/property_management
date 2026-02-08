# Phase 3: Client & Vendor Management (Admin Portal)
## Duration: 3 weeks | Priority: High

[← Back to Implementation Plan](README.md) | [← Phase 2](phase_2.md) | [Next Phase: Dispatch & Operations →](phase_4.md)

---

## Overview

**Goal**: Build comprehensive client and vendor management features within the **admin portal**. Admin users gain enhanced tools to manage client accounts, vendor relationships, COI tracking, and bidding workflows—all within the existing admin interface.

**Business Impact**: High - Enables complete client/vendor lifecycle management and testing before building self-service portals.

**Dependencies**:
- Backend Client Service (Port 8002) ✅ Ready
- Backend Vendor Service (Port 8002) ✅ Ready  
- Backend Documents Service (Port 8005) ✅ Ready
- Backend Charter Service (Port 8001) ✅ Ready
- Phase 1 & 2 Complete

**Team Allocation**:
- **Senior Dev** (2 weeks): Bidding workflows, payment management, COI validation
- **Junior Dev** (3 weeks): Client/vendor CRUD, enhanced detail views, UI components

**⚠️ Critical Note**: This phase builds ALL features in the **admin portal**. Separate client/vendor self-service portals will be created in **Phase 7** after the admin portal is fully tested end-to-end. Admin users have access to ALL capabilities across all roles.

---

## Week 1: Enhanced Client Management (Admin View)

### Feature 3.1: Client Account Management

**Estimated Time**: 3 days | **Developer**: Junior Dev

**Goal**: Enhance the existing client management pages to give admins complete visibility into client accounts, trip history, payments, and documents.

---

#### Task 3.1.1: Enhance Client Detail Page (4 hours)

Update existing `frontend/src/pages/clients/ClientDetail.tsx` to add tabbed interface:

```typescript
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Box,
  Paper,
  Tabs,
  Tab,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Chip
} from '@mui/material'
import {
  Edit as EditIcon,
  Block as BlockIcon,
  CheckCircle as ActiveIcon
} from '@mui/icons-material'
import { useQuery } from '@tanstack/react-query'
import api from '@/services/api'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props
  return (
    <div hidden={value !== index} {...other}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  )
}

export default function ClientDetail() {
  const { id } = useParams()
  const [tab, setTab] = useState(0)
  
  const { data: client } = useQuery({
    queryKey: ['clients', id],
    queryFn: async () => {
      const response = await api.get(`/api/v1/clients/${id}`)
      return response.data
    }
  })
  
  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4">
            {client?.name}
            {client?.company_name && ` (${client.company_name})`}
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Customer since {client?.created_at ? new Date(client.created_at).getFullYear() : '-'}
          </Typography>
        </Box>
        <Box>
          <Button
            variant="outlined"
            startIcon={<EditIcon />}
            sx={{ mr: 1 }}
          >
            Edit Info
          </Button>
          <Button
            variant="outlined"
            color={client?.account_status === 'active' ? 'error' : 'success'}
            startIcon={client?.account_status === 'active' ? <BlockIcon /> : <ActiveIcon />}
          >
            {client?.account_status === 'active' ? 'Suspend' : 'Activate'}
          </Button>
        </Box>
      </Box>
      
      {/* Summary Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Total Bookings
              </Typography>
              <Typography variant="h4">{client?.total_bookings || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Total Revenue
              </Typography>
              <Typography variant="h4">
                ${client?.total_revenue?.toLocaleString() || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Outstanding Balance
              </Typography>
              <Typography variant="h4" color={client?.outstanding_balance > 0 ? 'error.main' : 'success.main'}>
                ${client?.outstanding_balance?.toLocaleString() || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Account Status
              </Typography>
              <Chip
                label={client?.account_status || 'Active'}
                color={client?.account_status === 'active' ? 'success' : 'default'}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Tabs */}
      <Paper>
        <Tabs value={tab} onChange={(_, v) => setTab(v)}>
          <Tab label="Details" />
          <Tab label="Trip History" />
          <Tab label="Payments" />
          <Tab label="Documents" />
          <Tab label="Notes & Activity" />
        </Tabs>
        
        <TabPanel value={tab} index={0}>
          {/* Existing ClientDetail content */}
        </TabPanel>
        
        <TabPanel value={tab} index={1}>
          {/* Trip history - Task 3.1.2 */}
        </TabPanel>
        
        <TabPanel value={tab} index={2}>
          {/* Payment history - Task 3.1.3 */}
        </TabPanel>
        
        <TabPanel value={tab} index={3}>
          {/* Documents - Task 3.1.4 */}
        </TabPanel>
        
        <TabPanel value={tab} index={4}>
          {/* Notes/Activity log - Task 3.1.5 */}
        </TabPanel>
      </Paper>
    </Box>
  )
}
```

**What to do**:
1. Open `frontend/src/pages/clients/ClientDetail.tsx`
2. Import all necessary components from Material-UI
3. Add state for tab management: `const [tab, setTab] = useState(0)`
4. Add query for client data (already exists, just enhance it)
5. Wrap existing content in TabPanel for index 0
6. Add empty TabPanels for the other tabs (will be filled in next tasks)
7. Add summary cards at top showing key metrics
8. Add action buttons (Edit, Suspend/Activate)

**Backend API**: `GET /api/v1/clients/{id}` - Already exists ✅

---

#### Task 3.1.2: Client Trip History Tab (2 hours)

Create `frontend/src/features/clients/components/ClientTripsTab.tsx`:

```typescript
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  Typography,
  TextField,
  MenuItem
} from '@mui/material'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tantml:parameter>
import api from '@/services/api'
import { format } from 'date-fns'

interface ClientTripsTabProps {
  clientId: number
}

export default function ClientTripsTab({ clientId }: ClientTripsTabProps) {
  const navigate = useNavigate()
  const [statusFilter, setStatusFilter] = useState('all')
  
  const { data: trips } = useQuery({
    queryKey: ['client-trips', clientId, statusFilter],
    queryFn: async () => {
      const params = statusFilter !== 'all' ? `?status=${statusFilter}` : ''
      const response = await api.get(`/api/v1/clients/${clientId}/trips${params}`)
      return response.data
    }
  })
  
  const getStatusColor = (status: string): any => {
    const colors = {
      quote: 'info',
      approved: 'warning',
      booked: 'primary',
      confirmed: 'success',
      in_progress: 'secondary',
      completed: 'success',
      cancelled: 'error'
    }
    return colors[status as keyof typeof colors] || 'default'
  }
  
  return (
    <Box>
      {/* Filter */}
      <Box mb={2} display="flex" justifyContent="space-between" alignItems="center">
        <Typography variant="h6">
          Trip History ({trips?.length || 0} trips)
        </Typography>
        <TextField
          select
          size="small"
          label="Filter by Status"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          sx={{ minWidth: 200 }}
        >
          <MenuItem value="all">All Statuses</MenuItem>
          <MenuItem value="quote">Quotes</MenuItem>
          <MenuItem value="booked">Booked</MenuItem>
          <MenuItem value="completed">Completed</MenuItem>
          <MenuItem value="cancelled">Cancelled</MenuItem>
        </TextField>
      </Box>
      
      {/* Table */}
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Reference #</TableCell>
              <TableCell>Date</TableCell>
              <TableCell>Route</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Passengers</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Total Price</TableCell>
              <TableCell align="right">Balance Due</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {trips?.map((trip: any) => (
              <TableRow key={trip.id} hover>
                <TableCell>{trip.reference_number}</TableCell>
                <TableCell>
                  {format(new Date(trip.pickup_date), 'MMM dd, yyyy')}
                </TableCell>
                <TableCell>
                  <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                    {trip.pickup_location} → {trip.dropoff_location}
                  </Typography>
                </TableCell>
                <TableCell>{trip.trip_type}</TableCell>
                <TableCell>{trip.passengers}</TableCell>
                <TableCell>
                  <Chip
                    label={trip.status}
                    color={getStatusColor(trip.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell align="right">
                  ${trip.total_price?.toFixed(2) || '0.00'}
                </TableCell>
                <TableCell align="right">
                  <Typography
                    variant="body2"
                    color={trip.balance_due > 0 ? 'error.main' : 'success.main'}
                  >
                    ${trip.balance_due?.toFixed(2) || '0.00'}
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  <Button
                    size="small"
                    onClick={() => navigate(`/charters/${trip.charter_id}`)}
                  >
                    View
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      
      {trips?.length === 0 && (
        <Box textAlign="center" py={4}>
          <Typography color="textSecondary">
            No trips found for this client
          </Typography>
        </Box>
      )}
    </Box>
  )
}
```

**What to do**:
1. Create new file in `frontend/src/features/clients/components/ClientTripsTab.tsx`
2. Import it into `ClientDetail.tsx`
3. Use in TabPanel index 1: `<ClientTripsTab clientId={Number(id)} />`
4. Test with backend API

**Backend API**: `GET /api/v1/clients/{id}/trips?status={status}` - Already exists ✅

---

#### Task 3.1.3: Client Payment History Tab (2 hours)

Create `frontend/src/features/clients/components/ClientPaymentsTab.tsx`:

```typescript
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Typography,
  Button,
  Tooltip
} from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import api from '@/services/api'
import { format } from 'date-fns'
import { Receipt as ReceiptIcon } from '@mui/icons-material'

interface ClientPaymentsTabProps {
  clientId: number
}

export default function ClientPaymentsTab({ clientId }: ClientPaymentsTabProps) {
  const { data: payments } = useQuery({
    queryKey: ['client-payments', clientId],
    queryFn: async () => {
      const response = await api.get(`/api/v1/clients/${clientId}/payments`)
      return response.data
    }
  })
  
  const getPaymentStatusColor = (status: string): any => {
    const colors = {
      completed: 'success',
      pending: 'warning',
      failed: 'error',
      refunded: 'default'
    }
    return colors[status as keyof typeof colors] || 'default'
  }
  
  const totalPaid = payments?.reduce((sum: number, p: any) => sum + (p.amount || 0), 0) || 0
  
  return (
    <Box>
      {/* Summary */}
      <Box mb={3} p={2} sx={{ bgcolor: 'background.default', borderRadius: 1 }}>
        <Typography variant="h6">
          Total Paid: ${totalPaid.toLocaleString()}
        </Typography>
      </Box>
      
      {/* Table */}
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Date</TableCell>
              <TableCell>Charter Reference</TableCell>
              <TableCell>Payment Method</TableCell>
              <TableCell align="right">Amount</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Transaction ID</TableCell>
              <TableCell align="center">Receipt</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {payments?.map((payment: any) => (
              <TableRow key={payment.id} hover>
                <TableCell>
                  {format(new Date(payment.payment_date), 'MMM dd, yyyy HH:mm')}
                </TableCell>
                <TableCell>{payment.charter_reference || '-'}</TableCell>
                <TableCell>
                  <Chip label={payment.payment_method} size="small" />
                </TableCell>
                <TableCell align="right">
                  ${payment.amount?.toFixed(2)}
                </TableCell>
                <TableCell>
                  <Chip
                    label={payment.status}
                    color={getPaymentStatusColor(payment.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Tooltip title={payment.transaction_id || 'No transaction ID'}>
                    <Typography variant="body2" noWrap sx={{ maxWidth: 150 }}>
                      {payment.transaction_id || '-'}
                    </Typography>
                  </Tooltip>
                </TableCell>
                <TableCell align="center">
                  {payment.receipt_url && (
                    <Button
                      size="small"
                      startIcon={<ReceiptIcon />}
                      onClick={() => window.open(payment.receipt_url, '_blank')}
                    >
                      View
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      
      {payments?.length === 0 && (
        <Box textAlign="center" py={4}>
          <Typography color="textSecondary">
            No payment history for this client
          </Typography>
        </Box>
      )}
    </Box>
  )
}
```

**What to do**:
1. Create new file in `frontend/src/features/clients/components/ClientPaymentsTab.tsx`
2. Import into `ClientDetail.tsx`
3. Use in TabPanel index 2: `<ClientPaymentsTab clientId={Number(id)} />`

**Backend API**: `GET /api/v1/clients/{id}/payments` - Already exists ✅

---

#### Testing Checklist Week 1:
- [ ] Client detail page loads with tabs
- [ ] Summary cards display correct data
- [ ] All 5 tabs are clickable
- [ ] Trip history tab shows client's trips
- [ ] Trip filter (by status) works
- [ ] Clicking "View" navigates to charter detail
- [ ] Payment history displays correctly
- [ ] Total paid amount calculates correctly
- [ ] Receipt link opens in new tab
- [ ] Empty states show when no data
- [ ] Edit/Suspend buttons present (functionality in later phase)

---

## Week 2: Vendor Management & COI Tracking (Admin View)

### Feature 3.2: Enhanced Vendor Management

**Estimated Time**: 3 days | **Developer**: Junior Dev + Senior Dev

**Goal**: Give admins complete control over vendor management, including COI tracking, performance metrics, and assignment history.

---

#### Task 3.2.1: Enhance Vendor Detail Page (4 hours)

Update existing `frontend/src/pages/vendors/VendorDetail.tsx`:

```typescript
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Box,
  Paper,
  Tabs,
  Tab,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
  Alert
} from '@mui/material'
import {
  Edit as EditIcon,
  Warning as WarningIcon,
  CheckCircle as ActiveIcon
} from '@mui/icons-material'
import { useQuery } from '@tanstack/react-query'
import api from '@/services/api'
import { differenceInDays } from 'date-fns'

// TabPanel component same as ClientDetail

export default function VendorDetail() {
  const { id } = useParams()
  const [tab, setTab] = useState(0)
  
  const { data: vendor } = useQuery({
    queryKey: ['vendors', id],
    queryFn: async () => {
      const response = await api.get(`/api/v1/vendors/${id}`)
      return response.data
    }
  })
  
  // Check COI expiration
  const coiDaysRemaining = vendor?.coi_expiration_date
    ? differenceInDays(new Date(vendor.coi_expiration_date), new Date())
    : null
  
  const coiStatus = coiDaysRemaining === null
    ? { label: 'Missing', color: 'error', alert: true }
    : coiDaysRemaining < 0
    ? { label: 'Expired', color: 'error', alert: true }
    : coiDaysRemaining <= 30
    ? { label: 'Expiring Soon', color: 'warning', alert: true }
    : { label: 'Active', color: 'success', alert: false }
  
  return (
    <Box>
      {/* COI Alert */}
      {coiStatus.alert && (
        <Alert severity={coiStatus.color as any} sx={{ mb: 2 }}>
          <strong>COI {coiStatus.label}!</strong> This vendor cannot be assigned to new trips until COI is updated.
        </Alert>
      )}
      
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4">{vendor?.company_name}</Typography>
          <Typography variant="body2" color="textSecondary">
            Vendor ID: {vendor?.id} | MC#: {vendor?.mc_number || 'N/A'}
          </Typography>
        </Box>
        <Button variant="outlined" startIcon={<EditIcon />}>
          Edit Vendor
        </Button>
      </Box>
      
      {/* Summary Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Total Trips
              </Typography>
              <Typography variant="h4">{vendor?.total_trips || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Total Paid
              </Typography>
              <Typography variant="h4">
                ${vendor?.total_paid?.toLocaleString() || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                On-Time Rate
              </Typography>
              <Typography
                variant="h4"
                color={vendor?.on_time_rate >= 90 ? 'success.main' : vendor?.on_time_rate >= 75 ? 'warning.main' : 'error.main'}
              >
                {vendor?.on_time_rate?.toFixed(1) || 0}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                COI Status
              </Typography>
              <Chip
                label={coiStatus.label}
                color={coiStatus.color as any}
                icon={coiStatus.color === 'success' ? <ActiveIcon /> : <WarningIcon />}
              />
              {coiDaysRemaining !== null && coiDaysRemaining > 0 && (
                <Typography variant="caption" display="block" mt={1}>
                  {coiDaysRemaining} days remaining
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Tabs */}
      <Paper>
        <Tabs value={tab} onChange={(_, v) => setTab(v)}>
          <Tab label="Details" />
          <Tab label="Vehicles" />
          <Tab label="Drivers" />
          <Tab label="COI Documents" />
          <Tab label="Assignments" />
          <Tab label="Performance" />
        </Tabs>
        
        <TabPanel value={tab} index={0}>
          {/* Existing vendor details */}
        </TabPanel>
        
        <TabPanel value={tab} index={1}>
          {/* Vehicles - Task 3.2.2 */}
        </TabPanel>
        
        <TabPanel value={tab} index={2}>
          {/* Drivers - Task 3.2.3 */}
        </TabPanel>
        
        <TabPanel value={tab} index={3}>
          {/* COI Documents - Task 3.2.4 */}
        </TabPanel>
        
        <TabPanel value={tab} index={4}>
          {/* Assignments history - Task 3.2.5 */}
        </TabPanel>
        
        <TabPanel value={tab} index={5}>
          {/* Performance metrics - Task 3.2.6 */}
        </TabPanel>
      </Paper>
    </Box>
  )
}
```

**What to do**:
1. Open `frontend/src/pages/vendors/VendorDetail.tsx`
2. Add COI expiration calculation
3. Add alert for expired/expiring COI
4. Add summary cards with key metrics
5. Add tabs (6 tabs total)
6. Import `differenceInDays` from `date-fns`

**Backend API**: `GET /api/v1/vendors/{id}` - Already exists ✅

---

#### Task 3.2.2: COI Management Tab (4 hours) - **Senior Dev**

Create `frontend/src/features/vendors/components/COIManagement.tsx`:

```typescript
import { useState } from 'react'
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Button,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Typography
} from '@mui/material'
import {
  CloudUpload as UploadIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  Warning as WarningIcon,
  CheckCircle as ActiveIcon
} from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import api from '@/services/api'
import { format, differenceInDays } from 'date-fns'

interface COIManagementProps {
  vendorId: number
}

export default function COIManagement({ vendorId }: COIManagementProps) {
  const queryClient = useQueryClient()
  const [uploadDialog, setUploadDialog] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [expirationDate, setExpirationDate] = useState('')
  
  const { data: coiDocuments } = useQuery({
    queryKey: ['vendor-coi', vendorId],
    queryFn: async () => {
      const response = await api.get(`/api/v1/vendors/${vendorId}/coi`)
      return response.data
    }
  })
  
  const uploadMutation = useMutation({
    mutationFn: async () => {
      const formData = new FormData()
      if (selectedFile) {
        formData.append('file', selectedFile)
        formData.append('expiration_date', expirationDate)
      }
      return api.post(`/api/v1/vendors/${vendorId}/coi/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendor-coi', vendorId] })
      queryClient.invalidateQueries({ queryKey: ['vendors', vendorId.toString()] })
      toast.success('COI uploaded successfully')
      setUploadDialog(false)
      setSelectedFile(null)
      setExpirationDate('')
    },
    onError: () => {
      toast.error('Failed to upload COI')
    }
  })
  
  const deleteMutation = useMutation({
    mutationFn: (docId: number) => api.delete(`/api/v1/vendors/${vendorId}/coi/${docId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendor-coi', vendorId] })
      queryClient.invalidateQueries({ queryKey: ['vendors', vendorId.toString()] })
      toast.success('COI deleted')
    }
  })
  
  const getCOIStatus = (expirationDate: string) => {
    const daysUntilExpiration = differenceInDays(new Date(expirationDate), new Date())
    
    if (daysUntilExpiration < 0) {
      return { label: 'Expired', color: 'error' as const, icon: <WarningIcon />, days: daysUntilExpiration }
    } else if (daysUntilExpiration <= 30) {
      return { label: 'Expiring Soon', color: 'warning' as const, icon: <WarningIcon />, days: daysUntilExpiration }
    } else {
      return { label: 'Active', color: 'success' as const, icon: <ActiveIcon />, days: daysUntilExpiration }
    }
  }
  
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0])
    }
  }
  
  const hasExpiredCOI = coiDocuments?.some((doc: any) => {
    const daysLeft = differenceInDays(new Date(doc.expiration_date), new Date())
    return daysLeft < 0
  })
  
  return (
    <Box>
      {/* Alert */}
      {hasExpiredCOI && (
        <Alert severity="error" sx={{ mb: 2 }}>
          This vendor has expired COI documents and cannot be assigned to new trips.
        </Alert>
      )}
      
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">COI Documents</Typography>
        <Button
          variant="contained"
          startIcon={<UploadIcon />}
          onClick={() => setUploadDialog(true)}
        >
          Upload COI
        </Button>
      </Box>
      
      {/* Table */}
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>File Name</TableCell>
            <TableCell>Upload Date</TableCell>
            <TableCell>Expiration Date</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Days Remaining</TableCell>
            <TableCell align="center">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {coiDocuments?.map((doc: any) => {
            const status = getCOIStatus(doc.expiration_date)
            
            return (
              <TableRow key={doc.id}>
                <TableCell>{doc.filename}</TableCell>
                <TableCell>
                  {format(new Date(doc.uploaded_at), 'MMM dd, yyyy')}
                </TableCell>
                <TableCell>
                  {format(new Date(doc.expiration_date), 'MMM dd, yyyy')}
                </TableCell>
                <TableCell>
                  <Chip
                    label={status.label}
                    color={status.color}
                    icon={status.icon}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Typography
                    variant="body2"
                    color={status.days < 0 ? 'error.main' : status.days <= 30 ? 'warning.main' : 'textPrimary'}
                  >
                    {status.days < 0 ? `Expired ${Math.abs(status.days)} days ago` : `${status.days} days`}
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  <IconButton
                    size="small"
                    onClick={() => window.open(doc.file_url, '_blank')}
                    title="Download"
                  >
                    <DownloadIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => {
                      if (confirm('Delete this COI document?')) {
                        deleteMutation.mutate(doc.id)
                      }
                    }}
                    title="Delete"
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
      
      {coiDocuments?.length === 0 && (
        <Box textAlign="center" py={4}>
          <Typography color="textSecondary">
            No COI documents on file
          </Typography>
        </Box>
      )}
      
      {/* Upload Dialog */}
      <Dialog open={uploadDialog} onClose={() => setUploadDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Upload COI Document</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Button
              variant="outlined"
              component="label"
              fullWidth
              sx={{ mb: 2, py: 2 }}
            >
              {selectedFile ? selectedFile.name : 'Select PDF, JPG, or PNG'}
              <input
                type="file"
                hidden
                accept=".pdf,.jpg,.jpeg,.png"
                onChange={handleFileSelect}
              />
            </Button>
            
            <TextField
              fullWidth
              type="date"
              label="Expiration Date"
              value={expirationDate}
              onChange={(e) => setExpirationDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
              required
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={() => uploadMutation.mutate()}
            disabled={!selectedFile || !expirationDate || uploadMutation.isPending}
          >
            {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
```

**What to do**:
1. Create new file in `frontend/src/features/vendors/components/COIManagement.tsx`
2. Import into `VendorDetail.tsx`
3. Use in TabPanel index 3: `<COIManagement vendorId={Number(id)} />`
4. Install `react-hot-toast` if not already: `npm install react-hot-toast`
5. Add toast provider to app root (see README.md)

**Backend APIs**:
- `GET /api/v1/vendors/{id}/coi` - Get COI list ✅
- `POST /api/v1/vendors/{id}/coi/upload` - Upload COI ✅
- `DELETE /api/v1/vendors/{id}/coi/{doc_id}` - Delete COI ✅

---

#### Testing Checklist Week 2:
- [ ] Vendor detail page loads with tabs
- [ ] COI alert shows when expired/expiring
- [ ] Summary cards show correct data
- [ ] On-time rate color-coded (green/yellow/red)
- [ ] COI tab displays all documents
- [ ] COI status calculated correctly (active/expiring/expired)
- [ ] Days remaining accurate
- [ ] Upload dialog opens
- [ ] File selection works
- [ ] COI upload succeeds
- [ ] COI download works
- [ ] COI delete works with confirmation
- [ ] Toast notifications appear
- [ ] Vendor data refreshes after COI upload/delete

---

## Week 3: Vendor Bidding & Assignment (Admin Management)

### Feature 3.3: Vendor Bidding Management (Admin Oversight)

**Estimated Time**: 3 days | **Developer**: Senior Dev

**Goal**: Enable admins to manage vendor bidding process - invite vendors to bid, review submitted bids, accept/reject bids, and assign vendors to charters.

---

#### Task 3.3.1: Vendor Bidding Tab in Charter Detail (4 hours)

Add bidding tab to existing `frontend/src/pages/charters/CharterDetail.tsx`:

```typescript
// In CharterDetail.tsx, add new tab
<Tab label="Vendor Bids" />

// Add TabPanel
<TabPanel value={tab} index={7}>
  <VendorBiddingPanel charterId={charter.id} />
</TabPanel>
```

Create `frontend/src/features/charters/components/VendorBiddingPanel.tsx`:

```typescript
import { useState } from 'react'
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Button,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Typography,
  Alert,
  TextField
} from '@mui/material'
import {
  CheckCircle as AcceptIcon,
  Cancel as RejectIcon,
  Add as AddIcon,
  Email as EmailIcon
} from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import api from '@/services/api'
import { format } from 'date-fns'

interface VendorBiddingPanelProps {
  charterId: number
}

export default function VendorBiddingPanel({ charterId }: VendorBiddingPanelProps) {
  const queryClient = useQueryClient()
  const [inviteDialog, setInviteDialog] = useState(false)
  const [selectedVendors, setSelectedVendors] = useState<number[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  
  // Get existing bids
  const { data: bids } = useQuery({
    queryKey: ['charter-bids', charterId],
    queryFn: async () => {
      const response = await api.get(`/api/v1/charters/${charterId}/bids`)
      return response.data
    }
  })
  
  // Get available vendors for bidding
  const { data: vendors } = useQuery({
    queryKey: ['vendors-for-bidding'],
    queryFn: async () => {
      const response = await api.get('/api/v1/vendors?status=active&coi_valid=true')
      return response.data
    },
    enabled: inviteDialog
  })
  
  // Invite vendors to bid
  const inviteMutation = useMutation({
    mutationFn: async () => {
      return api.post(`/api/v1/charters/${charterId}/bids/invite`, {
        vendor_ids: selectedVendors
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['charter-bids', charterId] })
      toast.success(`Invited ${selectedVendors.length} vendor(s) to bid`)
      setInviteDialog(false)
      setSelectedVendors([])
    },
    onError: () => {
      toast.error('Failed to invite vendors')
    }
  })
  
  // Accept a bid
  const acceptBidMutation = useMutation({
    mutationFn: (bidId: number) => api.post(`/api/v1/charters/${charterId}/bids/${bidId}/accept`),
    onSuccess: (_, bidId) => {
      queryClient.invalidateQueries({ queryKey: ['charter-bids', charterId] })
      queryClient.invalidateQueries({ queryKey: ['charters', charterId.toString()] })
      toast.success('Bid accepted! Vendor assigned to charter.')
    },
    onError: () => {
      toast.error('Failed to accept bid')
    }
  })
  
  // Reject a bid
  const rejectBidMutation = useMutation({
    mutationFn: (bidId: number) => api.post(`/api/v1/charters/${charterId}/bids/${bidId}/reject`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['charter-bids', charterId] })
      toast.success('Bid rejected')
    },
    onError: () => {
      toast.error('Failed to reject bid')
    }
  })
  
  const getBidStatusColor = (status: string): any => {
    const colors = {
      pending: 'warning',
      submitted: 'info',
      accepted: 'success',
      rejected: 'error'
    }
    return colors[status as keyof typeof colors] || 'default'
  }
  
  const filteredVendors = vendors?.filter((v: any) =>
    v.company_name.toLowerCase().includes(searchTerm.toLowerCase())
  )
  
  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">Vendor Bids ({bids?.length || 0})</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setInviteDialog(true)}
        >
          Invite Vendors
        </Button>
      </Box>
      
      {/* Info Alert */}
      {bids?.some((b: any) => b.status === 'submitted') && (
        <Alert severity="info" sx={{ mb: 2 }}>
          You have {bids.filter((b: any) => b.status === 'submitted').length} bid(s) awaiting review.
        </Alert>
      )}
      
      {/* Bids Table */}
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Vendor</TableCell>
            <TableCell>Bid Amount</TableCell>
            <TableCell>Vehicle Type</TableCell>
            <TableCell>Submitted</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Notes</TableCell>
            <TableCell align="center">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {bids?.length === 0 ? (
            <TableRow>
              <TableCell colSpan={7} align="center">
                <Typography color="textSecondary" py={2}>
                  No bids yet. Invite vendors to bid on this charter.
                </Typography>
              </TableCell>
            </TableRow>
          ) : (
            bids?.map((bid: any) => (
              <TableRow key={bid.id}>
                <TableCell>
                  <Typography variant="body2">{bid.vendor_name}</Typography>
                  <Typography variant="caption" color="textSecondary">
                    On-Time: {bid.vendor_on_time_rate}% | COI: {bid.vendor_coi_status}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body1" fontWeight="bold">
                    ${bid.bid_amount?.toFixed(2) || 'Pending'}
                  </Typography>
                </TableCell>
                <TableCell>{bid.vehicle_type || '-'}</TableCell>
                <TableCell>
                  {bid.submitted_at ? format(new Date(bid.submitted_at), 'MMM dd, HH:mm') : 'Not submitted'}
                </TableCell>
                <TableCell>
                  <Chip
                    label={bid.status}
                    color={getBidStatusColor(bid.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                    {bid.notes || '-'}
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  {bid.status === 'submitted' && (
                    <Box>
                      <IconButton
                        size="small"
                        color="success"
                        onClick={() => {
                          if (confirm(`Accept bid from ${bid.vendor_name} for $${bid.bid_amount}?`)) {
                            acceptBidMutation.mutate(bid.id)
                          }
                        }}
                        title="Accept Bid"
                      >
                        <AcceptIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => {
                          if (confirm(`Reject bid from ${bid.vendor_name}?`)) {
                            rejectBidMutation.mutate(bid.id)
                          }
                        }}
                        title="Reject Bid"
                      >
                        <RejectIcon />
                      </IconButton>
                    </Box>
                  )}
                  {bid.status === 'pending' && (
                    <Chip label="Awaiting vendor" size="small" />
                  )}
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
      
      {/* Invite Vendors Dialog */}
      <Dialog open={inviteDialog} onClose={() => setInviteDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Invite Vendors to Bid</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            placeholder="Search vendors..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            sx={{ mb: 2, mt: 1 }}
          />
          
          <List sx={{ maxHeight: 400, overflow: 'auto' }}>
            {filteredVendors?.map((vendor: any) => (
              <ListItem key={vendor.id} divider>
                <ListItemText
                  primary={vendor.company_name}
                  secondary={
                    <>
                      COI: {vendor.coi_status} | 
                      On-Time: {vendor.on_time_rate}% | 
                      Vehicles: {vendor.total_vehicles}
                    </>
                  }
                />
                <ListItemSecondaryAction>
                  <Button
                    size="small"
                    variant={selectedVendors.includes(vendor.id) ? 'contained' : 'outlined'}
                    onClick={() => {
                      setSelectedVendors(prev =>
                        prev.includes(vendor.id)
                          ? prev.filter(id => id !== vendor.id)
                          : [...prev, vendor.id]
                      )
                    }}
                  >
                    {selectedVendors.includes(vendor.id) ? 'Selected' : 'Select'}
                  </Button>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
          
          {filteredVendors?.length === 0 && (
            <Typography color="textSecondary" align="center" py={4}>
              No vendors found. Make sure vendors have active COI.
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInviteDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            startIcon={<EmailIcon />}
            onClick={() => inviteMutation.mutate()}
            disabled={selectedVendors.length === 0 || inviteMutation.isPending}
          >
            {inviteMutation.isPending
              ? 'Sending invites...'
              : `Invite ${selectedVendors.length} Vendor(s)`}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
```

**What to do**:
1. Create new file in `frontend/src/features/charters/components/VendorBiddingPanel.tsx`
2. Open `frontend/src/pages/charters/CharterDetail.tsx`
3. Add new tab "Vendor Bids"
4. Import and use `VendorBiddingPanel` component
5. Adjust tab index numbers if needed

**Backend APIs**:
- `GET /api/v1/charters/{id}/bids` - Get bids ✅
- `GET /api/v1/vendors?status=active&coi_valid=true` - Get vendors ✅
- `POST /api/v1/charters/{id}/bids/invite` - Invite vendors ✅
- `POST /api/v1/charters/{id}/bids/{bid_id}/accept` - Accept bid ✅
- `POST /api/v1/charters/{id}/bids/{bid_id}/reject` - Reject bid ✅

---

#### Testing Checklist Week 3:
- [ ] Vendor bids tab appears in charter detail
- [ ] Bids table displays all invited vendors
- [ ] Bid status shown correctly (pending/submitted/accepted/rejected)
- [ ] Invite vendors dialog opens
- [ ] Vendor search works
- [ ] Vendor selection/deselection works
- [ ] Only vendors with valid COI shown
- [ ] Invite button sends invitations
- [ ] Accept bid assigns vendor to charter
- [ ] Reject bid updates status
- [ ] Toast notifications work
- [ ] Charter detail refreshes after accept
- [ ] Vendor performance metrics shown in bid list
- [ ] Empty state shows when no bids

---

## Deliverables Checklist

**Client Management (Admin Portal):**
- [ ] Enhanced client detail page with tabs
- [ ] Client trip history tab with filtering
- [ ] Client payment history tab
- [ ] Client documents tab (placeholder)
- [ ] Client notes/activity log tab (placeholder)
- [ ] Summary cards (bookings, revenue, balance, status)
- [ ] Edit/suspend buttons (UI only, functionality later)

**Vendor Management (Admin Portal):**
- [ ] Enhanced vendor detail page with tabs
- [ ] Vendor vehicles tab (placeholder for Phase 4)
- [ ] Vendor drivers tab (placeholder for Phase 4)
- [ ] COI documents tab with full management
- [ ] Vendor assignments history tab (placeholder)
- [ ] Vendor performance metrics tab (placeholder)
- [ ] Summary cards (trips, paid, on-time rate, COI status)
- [ ] COI expiration alert

**COI Management:**
- [ ] COI document upload (admin on behalf of vendor)
- [ ] COI document list with status indicators
- [ ] Expiration tracking (30/60/90 day warnings)
- [ ] Expired COI alerts
- [ ] COI download functionality
- [ ] COI delete functionality
- [ ] COI status affects vendor assignment eligibility

**Vendor Bidding:**
- [ ] Vendor bidding tab in charter detail
- [ ] Invite vendors to bid dialog
- [ ] Vendor search in invite dialog
- [ ] Bid list showing all invited vendors
- [ ] Bid status tracking (pending/submitted/accepted/rejected)
- [ ] Accept bid button (assigns vendor)
- [ ] Reject bid button
- [ ] Bid comparison (amount, vehicle type, vendor metrics)
- [ ] Email notifications (backend handles)

**Navigation & UX:**
- [ ] All tabs functional and navigable
- [ ] All routes configured correctly
- [ ] Toast notifications for all actions
- [ ] Loading states on all queries
- [ ] Error handling for all API calls
- [ ] Empty states where applicable
- [ ] Responsive design (mobile-friendly)

---

## Notes & Reminders

**⚠️ Critical Points:**

1. **Admin Portal Only**: All features in this phase are for the **admin portal**. No separate client/vendor portals are created yet.

2. **Admin Has Full Access**: Admins can:
   - View all client data (trips, payments, documents)
   - Manage vendor relationships and COI on their behalf
   - Oversee and manage the entire bidding process
   - Make all decisions (accept/reject bids, assign vendors)

3. **Testing Before Moving On**: After Phase 6 is complete, conduct full end-to-end testing of ALL admin portal features before starting Phase 7.

4. **Separate Portals in Phase 7**: Client and vendor self-service portals will be created in Phase 7, reusing many of these components with restricted permissions.

5. **Reusable Components**: Components like `ClientTripsTab`, `ClientPaymentsTab`, `COIManagement`, etc. are built to be reusable later in self-service portals.

6. **Backend Notifications**: When vendors are invited to bid or bids are accepted/rejected, the backend sends email notifications. Frontend just triggers the API.

7. **COI Validation**: The backend prevents assigning vendors with expired COI to new trips. The UI just reflects this business rule.

**Dependencies**:
- `react-hot-toast` for notifications
- `date-fns` for date calculations
- `@tanstack/react-query` for data fetching
- All Material-UI components

**File Structure**:
```
frontend/src/
├── pages/
│   ├── clients/
│   │   └── ClientDetail.tsx (enhanced)
│   ├── vendors/
│   │   └── VendorDetail.tsx (enhanced)
│   └── charters/
│       └── CharterDetail.tsx (add bidding tab)
└── features/
    ├── clients/
    │   └── components/
    │       ├── ClientTripsTab.tsx
    │       └── ClientPaymentsTab.tsx
    ├── vendors/
    │   └── components/
    │       └── COIManagement.tsx
    └── charters/
        └── components/
            └── VendorBiddingPanel.tsx
```

---

[← Back to Implementation Plan](README.md) | [← Phase 2](phase_2.md) | [Next Phase: Dispatch & Operations →](phase_4.md)
