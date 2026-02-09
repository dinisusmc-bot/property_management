/**
 * Enhanced Vendor Detail Page with Tabs
 */
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
  CircularProgress,
  Alert
} from '@mui/material'
import {
  Edit as EditIcon,
  Block as BlockIcon,
  CheckCircle as ActiveIcon
} from '@mui/icons-material'
import { useVendor, useSuspendVendor, useActivateVendor } from '../hooks/useVendorQuery'
import { TabPanel } from './VendorTabs'

export default function EnhancedVendorDetail() {
  const { id } = useParams<{ id: string }>()
  const vendorId = id ? parseInt(id, 10) : null
  const [tab, setTab] = useState(0)

  const { data: vendor, isLoading, error } = useVendor(vendorId!)
  const suspendMutation = useSuspendVendor(vendorId!)
  const activateMutation = useActivateVendor(vendorId!)

  const handleChangeTab = (_event: React.SyntheticEvent, newValue: number) => {
    setTab(newValue)
  }

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  if (error || !vendor) {
    return <Alert severity="error">Failed to load vendor</Alert>
  }

  const statusColor = (status: string) => {
    if (status === 'active') return 'success'
    if (status === 'suspended') return 'error'
    return 'default'
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4">
            {vendor.name}
            {vendor.company_name && ` (${vendor.company_name})`}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Vendor since {vendor.created_at ? new Date(vendor.created_at).getFullYear() : '-'}
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
            color={vendor.account_status === 'active' ? 'error' : 'success'}
            startIcon={vendor.account_status === 'active' ? <BlockIcon /> : <ActiveIcon />}
            onClick={vendor.account_status === 'active' ? () => suspendMutation.mutate() : () => activateMutation.mutate()}
            disabled={suspendMutation.isPending || activateMutation.isPending}
          >
            {vendor.account_status === 'active' ? 'Suspend' : 'Activate'}
          </Button>
        </Box>
      </Box>
      
      {/* Summary Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Total Bookings
              </Typography>
              <Typography variant="h4">{vendor.total_bookings || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Total Revenue
              </Typography>
              <Typography variant="h4">
                ${vendor.total_revenue?.toLocaleString() || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Outstanding Balance
              </Typography>
              <Typography variant="h4" color={vendor.outstanding_balance > 0 ? 'error.main' : 'success.main'}>
                ${vendor.outstanding_balance?.toLocaleString() || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Account Status
              </Typography>
              <Chip
                label={vendor.account_status}
                color={statusColor(vendor.account_status)}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Tabs */}
      <Paper>
        <Tabs value={tab} onChange={handleChangeTab}>
          <Tab label="Details" />
          <Tab label="COI Status" />
          <Tab label="Bidding History" />
          <Tab label="Documents" />
          <Tab label="Notes & Activity" />
        </Tabs>
        
        <TabPanel value={tab} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                Contact Information
              </Typography>
              <Typography variant="body1">{vendor.email}</Typography>
              <Typography variant="body1">{vendor.phone}</Typography>
              <Typography variant="body1">{vendor.address}</Typography>
              <Typography variant="body1">{vendor.city}, {vendor.state} {vendor.zip_code}</Typography>
            </Grid>
          </Grid>
        </TabPanel>
        
        <TabPanel value={tab} index={1}>
          <Typography variant="body1">COI status tab - To be implemented</Typography>
        </TabPanel>
        
        <TabPanel value={tab} index={2}>
          <Typography variant="body1">Bidding history tab - To be implemented</Typography>
        </TabPanel>
        
        <TabPanel value={tab} index={3}>
          <Typography variant="body1">Documents tab - To be implemented</Typography>
        </TabPanel>
        
        <TabPanel value={tab} index={4}>
          <Typography variant="body1">Notes & Activity tab - To be implemented</Typography>
        </TabPanel>
      </Paper>
    </Box>
  )
}
