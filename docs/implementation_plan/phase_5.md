# Phase 5: Accounting & Reporting
## Duration: 3 weeks | Priority: Medium

[← Back to Implementation Plan](README.md) | [← Phase 4](phase_4.md)

---

## Overview

**Goal**: Implement QuickBooks integration, advanced financial reports, automated invoicing, and payment reconciliation.

**Business Impact**: High - Critical for financial operations and accounting workflows.

**Dependencies**:
- Backend Accounting Service (Port 8003) ✅ Ready
- Backend Integrations Service (Port 8011) ✅ Ready
- Backend Charter Service (Port 8001) ✅ Ready

**Team Allocation**:
- **Senior Dev**: QuickBooks integration, complex reports
- **Junior Dev**: Invoice generation UI, report displays

---

## Week 1: QuickBooks Integration

### Feature 5.1: QuickBooks Sync Configuration

**Estimated Time**: 3 days

#### Step-by-Step Implementation

**Task 5.1.1: Create Accounting Feature Structure** (30 minutes)

```bash
mkdir -p frontend/src/features/accounting/components
mkdir -p frontend/src/features/accounting/hooks
mkdir -p frontend/src/features/accounting/api
mkdir -p frontend/src/features/accounting/types
```

**Task 5.1.2: Define Types** (1 hour)

Create `frontend/src/features/accounting/types/quickbooks.types.ts`:

```typescript
export interface QuickBooksConfig {
  id: number
  company_name: string
  realm_id: string
  is_connected: boolean
  last_sync: string | null
  auto_sync_enabled: boolean
  sync_frequency: 'hourly' | 'daily' | 'weekly' | 'manual'
}

export interface SyncHistory {
  id: number
  sync_type: 'customers' | 'invoices' | 'payments' | 'full'
  status: 'success' | 'failed' | 'in_progress'
  started_at: string
  completed_at: string | null
  records_synced: number
  error_message: string | null
}

export interface SyncMapping {
  id: number
  entity_type: 'client' | 'vendor' | 'charter'
  local_id: number
  quickbooks_id: string
  last_synced: string
}
```

**Task 5.1.3: Create API Service** (2 hours)

Create `frontend/src/features/accounting/api/quickbooksApi.ts`:

```typescript
import api from '@/services/api'
import { QuickBooksConfig, SyncHistory, SyncMapping } from '../types/quickbooks.types'

export const quickbooksApi = {
  getConfig: async () => {
    const response = await api.get<QuickBooksConfig>('/api/v1/integrations/quickbooks/config')
    return response.data
  },
  
  connect: async () => {
    // Returns OAuth URL
    const response = await api.get<{ auth_url: string }>('/api/v1/integrations/quickbooks/connect')
    return response.data
  },
  
  disconnect: async () => {
    await api.post('/api/v1/integrations/quickbooks/disconnect')
  },
  
  updateConfig: async (config: Partial<QuickBooksConfig>) => {
    const response = await api.patch('/api/v1/integrations/quickbooks/config', config)
    return response.data
  },
  
  syncNow: async (syncType: string) => {
    const response = await api.post<SyncHistory>('/api/v1/integrations/quickbooks/sync', {
      sync_type: syncType
    })
    return response.data
  },
  
  getSyncHistory: async () => {
    const response = await api.get<SyncHistory[]>('/api/v1/integrations/quickbooks/sync-history')
    return response.data
  },
  
  getMappings: async () => {
    const response = await api.get<SyncMapping[]>('/api/v1/integrations/quickbooks/mappings')
    return response.data
  }
}
```

**Task 5.1.4: Create QuickBooks Config Component** (4 hours)

Create `frontend/src/features/accounting/components/QuickBooksConfig.tsx`:

```typescript
import { useState } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  Switch,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Card,
  CardContent,
  Grid,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material'
import {
  CheckCircle as ConnectedIcon,
  Cancel as DisconnectedIcon,
  Sync as SyncIcon,
  Link as LinkIcon,
  LinkOff as UnlinkIcon
} from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { quickbooksApi } from '../api/quickbooksApi'
import { format } from 'date-fns'

export default function QuickBooksConfig() {
  const queryClient = useQueryClient()
  
  const { data: config, isLoading } = useQuery({
    queryKey: ['quickbooks-config'],
    queryFn: quickbooksApi.getConfig,
  })
  
  const { data: syncHistory } = useQuery({
    queryKey: ['quickbooks-sync-history'],
    queryFn: quickbooksApi.getSyncHistory,
  })
  
  const connectMutation = useMutation({
    mutationFn: quickbooksApi.connect,
    onSuccess: (data) => {
      // Open OAuth window
      window.location.href = data.auth_url
    },
    onError: () => {
      toast.error('Failed to initiate QuickBooks connection')
    }
  })
  
  const disconnectMutation = useMutation({
    mutationFn: quickbooksApi.disconnect,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quickbooks-config'] })
      toast.success('Disconnected from QuickBooks')
    },
    onError: () => {
      toast.error('Failed to disconnect')
    }
  })
  
  const syncMutation = useMutation({
    mutationFn: quickbooksApi.syncNow,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quickbooks-sync-history'] })
      toast.success('Sync started')
    },
    onError: () => {
      toast.error('Failed to start sync')
    }
  })
  
  const updateConfigMutation = useMutation({
    mutationFn: quickbooksApi.updateConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quickbooks-config'] })
      toast.success('Configuration updated')
    }
  })
  
  const getSyncStatusColor = (status: string): any => {
    const colors = {
      success: 'success',
      failed: 'error',
      in_progress: 'warning'
    }
    return colors[status as keyof typeof colors] || 'default'
  }
  
  if (isLoading) return <Box>Loading...</Box>
  
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        QuickBooks Integration
      </Typography>
      
      {/* Connection Status */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Box display="flex" alignItems="center" gap={2}>
              {config?.is_connected ? (
                <>
                  <ConnectedIcon color="success" fontSize="large" />
                  <Box>
                    <Typography variant="h6">Connected</Typography>
                    <Typography variant="body2" color="textSecondary">
                      {config.company_name}
                    </Typography>
                    {config.last_sync && (
                      <Typography variant="caption" color="textSecondary">
                        Last synced: {format(new Date(config.last_sync), 'MMM dd, yyyy HH:mm')}
                      </Typography>
                    )}
                  </Box>
                </>
              ) : (
                <>
                  <DisconnectedIcon color="error" fontSize="large" />
                  <Box>
                    <Typography variant="h6">Not Connected</Typography>
                    <Typography variant="body2" color="textSecondary">
                      Connect to QuickBooks to sync your data
                    </Typography>
                  </Box>
                </>
              )}
            </Box>
            
            <Box display="flex" gap={2}>
              {config?.is_connected ? (
                <>
                  <Button
                    variant="outlined"
                    startIcon={<SyncIcon />}
                    onClick={() => syncMutation.mutate('full')}
                    disabled={syncMutation.isPending}
                  >
                    Sync Now
                  </Button>
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<UnlinkIcon />}
                    onClick={() => disconnectMutation.mutate()}
                  >
                    Disconnect
                  </Button>
                </>
              ) : (
                <Button
                  variant="contained"
                  startIcon={<LinkIcon />}
                  onClick={() => connectMutation.mutate()}
                  disabled={connectMutation.isPending}
                >
                  Connect to QuickBooks
                </Button>
              )}
            </Box>
          </Box>
        </CardContent>
      </Card>
      
      {/* Sync Settings */}
      {config?.is_connected && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Sync Settings
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Typography>Automatic Sync</Typography>
                <Switch
                  checked={config.auto_sync_enabled}
                  onChange={(e) =>
                    updateConfigMutation.mutate({ auto_sync_enabled: e.target.checked })
                  }
                />
              </Box>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Sync Frequency</InputLabel>
                <Select
                  value={config.sync_frequency}
                  label="Sync Frequency"
                  onChange={(e) =>
                    updateConfigMutation.mutate({ sync_frequency: e.target.value as any })
                  }
                  disabled={!config.auto_sync_enabled}
                >
                  <MenuItem value="hourly">Hourly</MenuItem>
                  <MenuItem value="daily">Daily</MenuItem>
                  <MenuItem value="weekly">Weekly</MenuItem>
                  <MenuItem value="manual">Manual Only</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Paper>
      )}
      
      {/* Sync History */}
      {config?.is_connected && (
        <Paper>
          <Box p={2}>
            <Typography variant="h6" gutterBottom>
              Sync History
            </Typography>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Started</TableCell>
                  <TableCell>Completed</TableCell>
                  <TableCell>Records</TableCell>
                  <TableCell>Error</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {syncHistory?.map((sync) => (
                  <TableRow key={sync.id}>
                    <TableCell>{sync.sync_type}</TableCell>
                    <TableCell>
                      <Chip
                        label={sync.status}
                        color={getSyncStatusColor(sync.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {format(new Date(sync.started_at), 'MMM dd, HH:mm')}
                    </TableCell>
                    <TableCell>
                      {sync.completed_at
                        ? format(new Date(sync.completed_at), 'MMM dd, HH:mm')
                        : '-'}
                    </TableCell>
                    <TableCell>{sync.records_synced}</TableCell>
                    <TableCell>
                      {sync.error_message ? (
                        <Typography variant="caption" color="error">
                          {sync.error_message}
                        </Typography>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}
    </Box>
  )
}
```

**Task 5.1.5: Add Route** (15 minutes)

Update `frontend/src/App.tsx`:

```typescript
import QuickBooksConfig from './features/accounting/components/QuickBooksConfig'

<Route
  path="/accounting/quickbooks"
  element={
    <ProtectedRoute>
      <Layout>
        <NonVendorRoute>
          <QuickBooksConfig />
        </NonVendorRoute>
      </Layout>
    </ProtectedRoute>
  }
/>
```

**Testing Checklist**:
- [ ] Config page loads
- [ ] Connection status displays correctly
- [ ] Connect button initiates OAuth
- [ ] Disconnect button works
- [ ] Sync now button triggers sync
- [ ] Auto-sync toggle works
- [ ] Sync frequency dropdown works
- [ ] Sync history table displays
- [ ] Status chips colored correctly
- [ ] Error messages shown

---

## Week 2: Financial Reports

### Feature 5.2: Advanced Reports

**Estimated Time**: 3 days

#### Implementation Tasks

**Task 5.2.1: Report Dashboard** (4 hours)

Create `frontend/src/features/accounting/components/ReportDashboard.tsx`:

```typescript
import { useState } from 'react'
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActionArea,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  CircularProgress
} from '@mui/material'
import {
  Assessment as ReportIcon,
  Download as DownloadIcon,
  PictureAsPdf as PdfIcon,
  TableChart as ExcelIcon
} from '@mui/icons-material'
import { useQuery } from '@tanstack/react-query'
import api from '@/services/api'
import { format } from 'date-fns'

interface ReportConfig {
  id: string
  name: string
  description: string
  icon: JSX.Element
  parameters: {
    name: string
    type: 'date' | 'select' | 'text'
    label: string
    options?: string[]
  }[]
}

const availableReports: ReportConfig[] = [
  {
    id: 'aging',
    name: 'Aging Report',
    description: 'Accounts receivable aging analysis',
    icon: <ReportIcon />,
    parameters: [
      { name: 'as_of_date', type: 'date', label: 'As Of Date' },
      { name: 'aging_periods', type: 'select', label: 'Periods', options: ['30', '60', '90'] }
    ]
  },
  {
    id: 'departed_trips',
    name: 'Departed Trips',
    description: 'Trips that have been completed',
    icon: <ReportIcon />,
    parameters: [
      { name: 'date_from', type: 'date', label: 'From Date' },
      { name: 'date_to', type: 'date', label: 'To Date' }
    ]
  },
  {
    id: 'unearned_revenue',
    name: 'Unearned Revenue',
    description: 'Payments received for future trips',
    icon: <ReportIcon />,
    parameters: [
      { name: 'as_of_date', type: 'date', label: 'As Of Date' }
    ]
  },
  {
    id: 'profit_by_client',
    name: 'Profit by Client',
    description: 'Profitability analysis per client',
    icon: <ReportIcon />,
    parameters: [
      { name: 'date_from', type: 'date', label: 'From Date' },
      { name: 'date_to', type: 'date', label: 'To Date' }
    ]
  },
  {
    id: 'vendor_performance',
    name: 'Vendor Performance',
    description: 'Vendor utilization and performance metrics',
    icon: <ReportIcon />,
    parameters: [
      { name: 'date_from', type: 'date', label: 'From Date' },
      { name: 'date_to', type: 'date', label: 'To Date' }
    ]
  },
  {
    id: 'revenue_forecast',
    name: 'Revenue Forecast',
    description: 'Future revenue projection based on bookings',
    icon: <ReportIcon />,
    parameters: [
      { name: 'months_ahead', type: 'select', label: 'Months', options: ['3', '6', '12'] }
    ]
  }
]

export default function ReportDashboard() {
  const [selectedReport, setSelectedReport] = useState<ReportConfig | null>(null)
  const [parameters, setParameters] = useState<Record<string, string>>({})
  const [isGenerating, setIsGenerating] = useState(false)
  
  const handleReportClick = (report: ReportConfig) => {
    setSelectedReport(report)
    setParameters({})
  }
  
  const handleGenerate = async (format: 'pdf' | 'excel') => {
    if (!selectedReport) return
    
    setIsGenerating(true)
    try {
      const response = await api.post(
        `/api/v1/accounting/reports/${selectedReport.id}`,
        { ...parameters, format },
        { responseType: 'blob' }
      )
      
      // Download file
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute(
        'download',
        `${selectedReport.id}_${format}_${format(new Date(), 'yyyy-MM-dd')}.${
          format === 'pdf' ? 'pdf' : 'xlsx'
        }`
      )
      document.body.appendChild(link)
      link.click()
      link.remove()
      
      setSelectedReport(null)
    } catch (error) {
      console.error('Failed to generate report:', error)
    } finally {
      setIsGenerating(false)
    }
  }
  
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Financial Reports
      </Typography>
      
      <Grid container spacing={3}>
        {availableReports.map((report) => (
          <Grid item xs={12} md={6} lg={4} key={report.id}>
            <Card>
              <CardActionArea onClick={() => handleReportClick(report)}>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={2} mb={2}>
                    {report.icon}
                    <Typography variant="h6">{report.name}</Typography>
                  </Box>
                  <Typography variant="body2" color="textSecondary">
                    {report.description}
                  </Typography>
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>
      
      {/* Report Parameters Dialog */}
      <Dialog
        open={!!selectedReport}
        onClose={() => setSelectedReport(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>{selectedReport?.name}</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              {selectedReport?.description}
            </Typography>
            
            <Grid container spacing={2} sx={{ mt: 2 }}>
              {selectedReport?.parameters.map((param) => (
                <Grid item xs={12} key={param.name}>
                  {param.type === 'date' ? (
                    <TextField
                      fullWidth
                      type="date"
                      label={param.label}
                      value={parameters[param.name] || ''}
                      onChange={(e) =>
                        setParameters({ ...parameters, [param.name]: e.target.value })
                      }
                      InputLabelProps={{ shrink: true }}
                    />
                  ) : param.type === 'select' ? (
                    <TextField
                      fullWidth
                      select
                      label={param.label}
                      value={parameters[param.name] || ''}
                      onChange={(e) =>
                        setParameters({ ...parameters, [param.name]: e.target.value })
                      }
                      SelectProps={{ native: true }}
                    >
                      <option value="">Select...</option>
                      {param.options?.map((opt) => (
                        <option key={opt} value={opt}>
                          {opt}
                        </option>
                      ))}
                    </TextField>
                  ) : (
                    <TextField
                      fullWidth
                      label={param.label}
                      value={parameters[param.name] || ''}
                      onChange={(e) =>
                        setParameters({ ...parameters, [param.name]: e.target.value })
                      }
                    />
                  )}
                </Grid>
              ))}
            </Grid>
            
            <Box display="flex" gap={2} mt={3}>
              <Button
                variant="outlined"
                fullWidth
                startIcon={isGenerating ? <CircularProgress size={20} /> : <PdfIcon />}
                onClick={() => handleGenerate('pdf')}
                disabled={isGenerating}
              >
                PDF
              </Button>
              <Button
                variant="contained"
                fullWidth
                startIcon={isGenerating ? <CircularProgress size={20} /> : <ExcelIcon />}
                onClick={() => handleGenerate('excel')}
                disabled={isGenerating}
              >
                Excel
              </Button>
            </Box>
          </Box>
        </DialogContent>
      </Dialog>
    </Box>
  )
}
```

**Task 5.2.2: Add Route** (15 minutes)

```typescript
<Route
  path="/accounting/reports"
  element={
    <ProtectedRoute>
      <Layout>
        <NonVendorRoute>
          <ReportDashboard />
        </NonVendorRoute>
      </Layout>
    </ProtectedRoute>
  }
/>
```

**Testing Checklist**:
- [ ] Report cards display
- [ ] Card click opens dialog
- [ ] Parameters render correctly
- [ ] Date pickers work
- [ ] Dropdowns populate
- [ ] PDF button triggers download
- [ ] Excel button triggers download
- [ ] Loading state shows
- [ ] File downloads with correct name

---

## Week 3: Automated Invoicing

### Feature 5.3: Invoice Generation

**Estimated Time**: 2 days

#### Implementation Tasks

**Task 5.3.1: Invoice Templates** (3 hours)

Create `frontend/src/features/accounting/components/InvoiceGenerator.tsx`:

```typescript
import { useState } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Grid,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableRow
} from '@mui/material'
import { Send as SendIcon, Download as DownloadIcon } from '@mui/icons-material'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import api from '@/services/api'

interface InvoiceGeneratorProps {
  charterId: number
  clientId: number
}

export default function InvoiceGenerator({ charterId, clientId }: InvoiceGeneratorProps) {
  const [dueDate, setDueDate] = useState('')
  const [notes, setNotes] = useState('')
  
  const generateMutation = useMutation({
    mutationFn: async (action: 'generate' | 'send') => {
      return api.post(`/api/v1/accounting/invoices/generate`, {
        charter_id: charterId,
        due_date: dueDate,
        notes,
        action
      })
    },
    onSuccess: (data, action) => {
      if (action === 'generate') {
        toast.success('Invoice generated and downloaded')
      } else {
        toast.success('Invoice sent to client')
      }
    },
    onError: () => {
      toast.error('Failed to generate invoice')
    }
  })
  
  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Generate Invoice
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            type="date"
            label="Due Date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
        </Grid>
        
        <Grid item xs={12}>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Additional notes to include on invoice..."
          />
        </Grid>
        
        <Grid item xs={12}>
          <Box display="flex" gap={2}>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={() => generateMutation.mutate('generate')}
              disabled={!dueDate || generateMutation.isPending}
            >
              Generate PDF
            </Button>
            <Button
              variant="contained"
              startIcon={<SendIcon />}
              onClick={() => generateMutation.mutate('send')}
              disabled={!dueDate || generateMutation.isPending}
            >
              Generate & Send
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Paper>
  )
}
```

**Testing Checklist**:
- [ ] Invoice form displays
- [ ] Due date required
- [ ] Generate PDF works
- [ ] Send email works
- [ ] Notes included in invoice
- [ ] Toast notifications show

---

## Deliverables Checklist

- [ ] QuickBooks OAuth connection
- [ ] Sync configuration UI
- [ ] Manual sync trigger
- [ ] Auto-sync settings
- [ ] Sync history display
- [ ] Entity mapping display
- [ ] Aging report
- [ ] Departed trips report
- [ ] Unearned revenue report
- [ ] Profit by client report
- [ ] Vendor performance report
- [ ] Revenue forecast report
- [ ] PDF export
- [ ] Excel export
- [ ] Invoice generation
- [ ] Invoice email sending
- [ ] All routes configured
- [ ] Error handling complete

---

[← Back to Implementation Plan](README.md) | [← Phase 4](phase_4.md) | [Next Phase: Analytics & Configuration →](phase_6.md)
