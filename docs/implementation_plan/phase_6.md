# Phase 6: Analytics & Configuration
## Duration: 3 weeks | Priority: Medium

[← Back to Implementation Plan](README.md) | [← Phase 5](phase_5.md)

---

## Overview

**Goal**: Build analytics dashboards with charts, configuration management UI for business rules, and user/permission management.

**Business Impact**: Medium - Provides business intelligence and system configurability.

**Dependencies**:
- Backend Analytics Service (Port 8013) ✅ Ready
- Backend Config Service (Port 8008) ✅ Ready
- Backend Auth Service (Port 8000) ✅ Ready

**Team Allocation**:
- **Senior Dev**: Analytics dashboards with charts, complex configurations
- **Junior Dev**: CRUD forms for configurations, permission UI

---

## Week 1: Analytics Dashboards

### Feature 6.1: Revenue Analytics Dashboard

**Estimated Time**: 3 days

#### Step-by-Step Implementation

**Task 6.1.1: Install Chart Library** (15 minutes)

```bash
cd frontend
npm install recharts
```

**Task 6.1.2: Create Analytics Feature Structure** (30 minutes)

```bash
mkdir -p frontend/src/features/analytics/components
mkdir -p frontend/src/features/analytics/hooks
mkdir -p frontend/src/features/analytics/api
mkdir -p frontend/src/features/analytics/types
```

**Task 6.1.3: Define Types** (1 hour)

Create `frontend/src/features/analytics/types/analytics.types.ts`:

```typescript
export interface RevenueMetrics {
  total_revenue: number
  total_profit: number
  average_profit_margin: number
  total_trips: number
  revenue_by_month: {
    month: string
    revenue: number
    profit: number
    trips: number
  }[]
  revenue_by_trip_type: {
    trip_type: string
    revenue: number
    count: number
  }[]
  top_clients: {
    client_id: number
    client_name: string
    revenue: number
    trips: number
  }[]
}

export interface SalesPipelineMetrics {
  total_leads: number
  total_quotes: number
  conversion_rate: number
  average_quote_value: number
  pipeline_by_stage: {
    stage: string
    count: number
    value: number
  }[]
  leads_by_source: {
    source: string
    count: number
  }[]
  conversion_funnel: {
    stage: string
    count: number
    conversion_rate: number
  }[]
}

export interface OperationsMetrics {
  total_trips_today: number
  in_transit: number
  completed_today: number
  on_time_percentage: number
  vendor_utilization: {
    vendor_id: number
    vendor_name: string
    trips_assigned: number
    utilization_rate: number
  }[]
  trips_by_status: {
    status: string
    count: number
  }[]
}

export interface DateFilter {
  start_date: string
  end_date: string
}
```

**Task 6.1.4: Create API Service** (1 hour)

Create `frontend/src/features/analytics/api/analyticsApi.ts`:

```typescript
import api from '@/services/api'
import { RevenueMetrics, SalesPipelineMetrics, OperationsMetrics, DateFilter } from '../types/analytics.types'

export const analyticsApi = {
  getRevenueMetrics: async (filter: DateFilter) => {
    const params = new URLSearchParams({
      start_date: filter.start_date,
      end_date: filter.end_date
    })
    const response = await api.get<RevenueMetrics>(`/api/v1/analytics/revenue?${params}`)
    return response.data
  },
  
  getSalesPipelineMetrics: async (filter: DateFilter) => {
    const params = new URLSearchParams({
      start_date: filter.start_date,
      end_date: filter.end_date
    })
    const response = await api.get<SalesPipelineMetrics>(`/api/v1/analytics/sales-pipeline?${params}`)
    return response.data
  },
  
  getOperationsMetrics: async () => {
    const response = await api.get<OperationsMetrics>('/api/v1/analytics/operations')
    return response.data
  }
}
```

**Task 6.1.5: Create Revenue Dashboard** (5 hours)

Create `frontend/src/features/analytics/components/RevenueDashboard.tsx`:

```typescript
import { useState } from 'react'
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  TextField
} from '@mui/material'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'
import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../api/analyticsApi'
import { format, subMonths } from 'date-fns'

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d']

export default function RevenueDashboard() {
  const [dateFilter, setDateFilter] = useState({
    start_date: format(subMonths(new Date(), 6), 'yyyy-MM-dd'),
    end_date: format(new Date(), 'yyyy-MM-dd')
  })
  
  const { data: metrics, isLoading } = useQuery({
    queryKey: ['revenue-metrics', dateFilter],
    queryFn: () => analyticsApi.getRevenueMetrics(dateFilter),
  })
  
  if (isLoading) return <Box>Loading...</Box>
  
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Revenue Analytics</Typography>
        <Box display="flex" gap={2}>
          <TextField
            size="small"
            type="date"
            label="Start Date"
            value={dateFilter.start_date}
            onChange={(e) => setDateFilter({ ...dateFilter, start_date: e.target.value })}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            size="small"
            type="date"
            label="End Date"
            value={dateFilter.end_date}
            onChange={(e) => setDateFilter({ ...dateFilter, end_date: e.target.value })}
            InputLabelProps={{ shrink: true }}
          />
        </Box>
      </Box>
      
      {/* Summary Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Revenue
              </Typography>
              <Typography variant="h4">
                ${metrics?.total_revenue.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Profit
              </Typography>
              <Typography variant="h4">
                ${metrics?.total_profit.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Profit Margin
              </Typography>
              <Typography variant="h4">
                {metrics?.average_profit_margin.toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Trips
              </Typography>
              <Typography variant="h4">
                {metrics?.total_trips}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Revenue Trend */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Revenue Trend
        </Typography>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={metrics?.revenue_by_month}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip formatter={(value) => `$${value}`} />
            <Legend />
            <Line type="monotone" dataKey="revenue" stroke="#8884d8" name="Revenue" />
            <Line type="monotone" dataKey="profit" stroke="#82ca9d" name="Profit" />
          </LineChart>
        </ResponsiveContainer>
      </Paper>
      
      {/* Revenue by Trip Type */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Revenue by Trip Type
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={metrics?.revenue_by_trip_type}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="trip_type" />
                <YAxis />
                <Tooltip formatter={(value) => `$${value}`} />
                <Bar dataKey="revenue" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Top Clients
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={metrics?.top_clients} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis type="category" dataKey="client_name" width={100} />
                <Tooltip formatter={(value) => `$${value}`} />
                <Bar dataKey="revenue" fill="#82ca9d" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
```

**Task 6.1.6: Create Sales Pipeline Dashboard** (3 hours)

Create `frontend/src/features/analytics/components/SalesPipelineDashboard.tsx`:

```typescript
import { useState } from 'react'
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  TextField
} from '@mui/material'
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  FunnelChart,
  Funnel,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'
import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../api/analyticsApi'
import { format, subMonths } from 'date-fns'

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8']

export default function SalesPipelineDashboard() {
  const [dateFilter, setDateFilter] = useState({
    start_date: format(subMonths(new Date(), 3), 'yyyy-MM-dd'),
    end_date: format(new Date(), 'yyyy-MM-dd')
  })
  
  const { data: metrics, isLoading } = useQuery({
    queryKey: ['sales-pipeline-metrics', dateFilter],
    queryFn: () => analyticsApi.getSalesPipelineMetrics(dateFilter),
  })
  
  if (isLoading) return <Box>Loading...</Box>
  
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Sales Pipeline</Typography>
        <Box display="flex" gap={2}>
          <TextField
            size="small"
            type="date"
            label="Start Date"
            value={dateFilter.start_date}
            onChange={(e) => setDateFilter({ ...dateFilter, start_date: e.target.value })}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            size="small"
            type="date"
            label="End Date"
            value={dateFilter.end_date}
            onChange={(e) => setDateFilter({ ...dateFilter, end_date: e.target.value })}
            InputLabelProps={{ shrink: true }}
          />
        </Box>
      </Box>
      
      {/* Summary Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Leads
              </Typography>
              <Typography variant="h4">{metrics?.total_leads}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Quotes
              </Typography>
              <Typography variant="h4">{metrics?.total_quotes}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Conversion Rate
              </Typography>
              <Typography variant="h4">
                {metrics?.conversion_rate.toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Avg Quote Value
              </Typography>
              <Typography variant="h4">
                ${metrics?.average_quote_value.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Pipeline by Stage */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Pipeline by Stage
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={metrics?.pipeline_by_stage}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="stage" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#8884d8" name="Count" />
                <Bar dataKey="value" fill="#82ca9d" name="Value ($)" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Leads by Source
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={metrics?.leads_by_source}
                  dataKey="count"
                  nameKey="source"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label
                >
                  {metrics?.leads_by_source.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
```

**Task 6.1.7: Add Routes** (15 minutes)

Update `frontend/src/App.tsx`:

```typescript
import RevenueDashboard from './features/analytics/components/RevenueDashboard'
import SalesPipelineDashboard from './features/analytics/components/SalesPipelineDashboard'

<Route path="/analytics/revenue" element={<ProtectedRoute><Layout><NonVendorRoute><RevenueDashboard /></NonVendorRoute></Layout></ProtectedRoute>} />
<Route path="/analytics/sales" element={<ProtectedRoute><Layout><NonVendorRoute><SalesPipelineDashboard /></NonVendorRoute></Layout></ProtectedRoute>} />
```

**Testing Checklist**:
- [ ] Revenue dashboard loads
- [ ] Summary cards display
- [ ] Line chart renders
- [ ] Bar charts render
- [ ] Date filter works
- [ ] Sales pipeline loads
- [ ] Pie chart renders
- [ ] All tooltips work
- [ ] Data refreshes on filter change

---

## Week 2: Configuration Management

### Feature 6.2: Promo Code Management

**Estimated Time**: 2 days

#### Implementation Tasks

**Task 6.2.1: Promo Code Types** (30 minutes)

Create `frontend/src/features/config/types/promo.types.ts`:

```typescript
export interface PromoCode {
  id: number
  code: string
  description: string
  discount_type: 'percentage' | 'fixed_amount'
  discount_value: number
  start_date: string
  end_date: string | null
  max_uses: number | null
  current_uses: number
  min_trip_value: number | null
  trip_types: string[] | null
  is_active: boolean
  created_at: string
}

export interface CreatePromoCodeRequest {
  code: string
  description: string
  discount_type: 'percentage' | 'fixed_amount'
  discount_value: number
  start_date: string
  end_date?: string
  max_uses?: number
  min_trip_value?: number
  trip_types?: string[]
}
```

**Task 6.2.2: Promo Code List** (3 hours)

Create `frontend/src/features/config/components/PromoCodeList.tsx`:

```typescript
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Chip,
  IconButton,
  Switch,
  Typography
} from '@mui/material'
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import api from '@/services/api'
import { PromoCode } from '../types/promo.types'
import { format } from 'date-fns'

export default function PromoCodeList() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  const { data: promoCodes, isLoading } = useQuery({
    queryKey: ['promo-codes'],
    queryFn: async () => {
      const response = await api.get<PromoCode[]>('/api/v1/config/promo-codes')
      return response.data
    }
  })
  
  const toggleActiveMutation = useMutation({
    mutationFn: (id: number) => api.patch(`/api/v1/config/promo-codes/${id}/toggle`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['promo-codes'] })
      toast.success('Promo code updated')
    }
  })
  
  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/api/v1/config/promo-codes/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['promo-codes'] })
      toast.success('Promo code deleted')
    }
  })
  
  if (isLoading) return <Box>Loading...</Box>
  
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Promo Codes</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/config/promo-codes/new')}
        >
          Add Promo Code
        </Button>
      </Box>
      
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Code</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Discount</TableCell>
              <TableCell>Valid Period</TableCell>
              <TableCell>Uses</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {promoCodes?.map((promo) => (
              <TableRow key={promo.id}>
                <TableCell>
                  <Typography fontWeight="bold">{promo.code}</Typography>
                </TableCell>
                <TableCell>{promo.description}</TableCell>
                <TableCell>
                  {promo.discount_type === 'percentage'
                    ? `${promo.discount_value}%`
                    : `$${promo.discount_value}`}
                </TableCell>
                <TableCell>
                  {format(new Date(promo.start_date), 'MMM dd, yyyy')}
                  {promo.end_date && ` - ${format(new Date(promo.end_date), 'MMM dd, yyyy')}`}
                </TableCell>
                <TableCell>
                  {promo.current_uses}
                  {promo.max_uses && ` / ${promo.max_uses}`}
                </TableCell>
                <TableCell>
                  <Switch
                    checked={promo.is_active}
                    onChange={() => toggleActiveMutation.mutate(promo.id)}
                  />
                </TableCell>
                <TableCell align="center">
                  <IconButton
                    size="small"
                    onClick={() => navigate(`/config/promo-codes/${promo.id}`)}
                  >
                    <EditIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => {
                      if (confirm('Delete this promo code?')) {
                        deleteMutation.mutate(promo.id)
                      }
                    }}
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}
```

**Testing Checklist**:
- [ ] Promo code list loads
- [ ] All fields display correctly
- [ ] Add button navigates
- [ ] Edit button navigates
- [ ] Toggle switch works
- [ ] Delete confirmation shows
- [ ] Delete works

---

## Week 3: User & Permission Management

### Feature 6.3: Permission Editor

**Estimated Time**: 3 days

#### Implementation Tasks

**Task 6.3.1: Permission Types** (30 minutes)

Create `frontend/src/features/admin/types/permission.types.ts`:

```typescript
export interface Permission {
  id: string
  name: string
  description: string
  category: 'charters' | 'clients' | 'vendors' | 'finance' | 'reports' | 'config'
}

export interface Role {
  id: number
  name: string
  description: string
  permissions: string[]
  is_system_role: boolean
  created_at: string
}

export interface User {
  id: number
  email: string
  name: string
  role: string
  role_id: number
  is_active: boolean
  last_login: string | null
  created_at: string
}
```

**Task 6.3.2: Role Editor Component** (4 hours)

Create `frontend/src/features/admin/components/RoleEditor.tsx`:

```typescript
import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  FormControl,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material'
import { ExpandMore as ExpandIcon, Save as SaveIcon } from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import api from '@/services/api'
import { Role, Permission } from '../types/permission.types'

export default function RoleEditor() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([])
  
  const { data: permissions } = useQuery({
    queryKey: ['permissions'],
    queryFn: async () => {
      const response = await api.get<Permission[]>('/api/v1/auth/permissions')
      return response.data
    }
  })
  
  const { data: role } = useQuery({
    queryKey: ['roles', id],
    queryFn: async () => {
      const response = await api.get<Role>(`/api/v1/auth/roles/${id}`)
      return response.data
    },
    enabled: !!id
  })
  
  useEffect(() => {
    if (role) {
      setName(role.name)
      setDescription(role.description)
      setSelectedPermissions(role.permissions)
    }
  }, [role])
  
  const saveMutation = useMutation({
    mutationFn: async () => {
      const data = { name, description, permissions: selectedPermissions }
      if (id) {
        return api.patch(`/api/v1/auth/roles/${id}`, data)
      } else {
        return api.post('/api/v1/auth/roles', data)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] })
      toast.success(`Role ${id ? 'updated' : 'created'} successfully`)
      navigate('/admin/roles')
    },
    onError: () => {
      toast.error(`Failed to ${id ? 'update' : 'create'} role`)
    }
  })
  
  const handlePermissionToggle = (permissionId: string) => {
    setSelectedPermissions((prev) =>
      prev.includes(permissionId)
        ? prev.filter((p) => p !== permissionId)
        : [...prev, permissionId]
    )
  }
  
  // Group permissions by category
  const permissionsByCategory = permissions?.reduce((acc, perm) => {
    if (!acc[perm.category]) {
      acc[perm.category] = []
    }
    acc[perm.category].push(perm)
    return acc
  }, {} as Record<string, Permission[]>)
  
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        {id ? 'Edit Role' : 'Create Role'}
      </Typography>
      
      <Paper sx={{ p: 3 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Role Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={role?.is_system_role}
            />
          </Grid>
          
          <Grid item xs={12}>
            <TextField
              fullWidth
              multiline
              rows={2}
              label="Description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </Grid>
          
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Permissions
            </Typography>
            
            {permissionsByCategory &&
              Object.entries(permissionsByCategory).map(([category, perms]) => (
                <Accordion key={category}>
                  <AccordionSummary expandIcon={<ExpandIcon />}>
                    <Typography textTransform="capitalize">{category}</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <FormGroup>
                      {perms.map((perm) => (
                        <FormControlLabel
                          key={perm.id}
                          control={
                            <Checkbox
                              checked={selectedPermissions.includes(perm.id)}
                              onChange={() => handlePermissionToggle(perm.id)}
                              disabled={role?.is_system_role}
                            />
                          }
                          label={
                            <Box>
                              <Typography variant="body2">{perm.name}</Typography>
                              <Typography variant="caption" color="textSecondary">
                                {perm.description}
                              </Typography>
                            </Box>
                          }
                        />
                      ))}
                    </FormGroup>
                  </AccordionDetails>
                </Accordion>
              ))}
          </Grid>
          
          <Grid item xs={12}>
            <Box display="flex" gap={2} justifyContent="flex-end">
              <Button variant="outlined" onClick={() => navigate('/admin/roles')}>
                Cancel
              </Button>
              <Button
                variant="contained"
                startIcon={<SaveIcon />}
                onClick={() => saveMutation.mutate()}
                disabled={!name || role?.is_system_role || saveMutation.isPending}
              >
                Save Role
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  )
}
```

**Testing Checklist**:
- [ ] Role editor loads
- [ ] Permissions grouped by category
- [ ] Checkboxes toggle
- [ ] System roles disabled
- [ ] Save button works
- [ ] Navigation works
- [ ] Toast notifications show

---

## Deliverables Checklist

- [ ] Revenue analytics dashboard
- [ ] Sales pipeline dashboard
- [ ] Operations dashboard
- [ ] Line charts working
- [ ] Bar charts working
- [ ] Pie charts working
- [ ] Date filters working
- [ ] Promo code CRUD
- [ ] Promo code activation toggle
- [ ] Pricing matrix editor
- [ ] Amenity management
- [ ] Role management UI
- [ ] Permission editor
- [ ] Custom role creation
- [ ] User-role assignment
- [ ] All routes configured
- [ ] Charts responsive

---

[← Back to Implementation Plan](README.md) | [← Phase 5](phase_5.md) | [Next Phase: Advanced Features & Polish →](phase_7.md)
