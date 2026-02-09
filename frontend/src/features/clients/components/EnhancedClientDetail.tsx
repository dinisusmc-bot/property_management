/**
 * Enhanced Client Detail Page with Tabs
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
import { useClient, useSuspendClient, useActivateClient } from '../hooks/useClientQuery'

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

export default function EnhancedClientDetail() {
  const { id } = useParams<{ id: string }>()
  const clientId = id ? parseInt(id, 10) : null
  const [tab, setTab] = useState(0)

  const { data: client, isLoading, error } = useClient(clientId!)
  const suspendMutation = useSuspendClient(clientId!)
  const activateMutation = useActivateClient(clientId!)

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

  if (error || !client) {
    return <Alert severity="error">Failed to load client</Alert>
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
            {client.name}
            {client.company_name && ` (${client.company_name})`}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Customer since {client.created_at ? new Date(client.created_at).getFullYear() : '-'}
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
            color={client.account_status === 'active' ? 'error' : 'success'}
            startIcon={client.account_status === 'active' ? <BlockIcon /> : <ActiveIcon />}
            onClick={client.account_status === 'active' ? () => suspendMutation.mutate() : () => activateMutation.mutate()}
            disabled={suspendMutation.isPending || activateMutation.isPending}
          >
            {client.account_status === 'active' ? 'Suspend' : 'Activate'}
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
              <Typography variant="h4">{client.total_bookings || 0}</Typography>
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
                ${client.total_revenue?.toLocaleString() || 0}
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
              <Typography variant="h4" color={client.outstanding_balance > 0 ? 'error.main' : 'success.main'}>
                ${client.outstanding_balance?.toLocaleString() || 0}
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
                label={client.account_status}
                color={statusColor(client.account_status)}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Tabs */}
      <Paper>
        <Tabs value={tab} onChange={handleChangeTab}>
          <Tab label="Details" />
          <Tab label="Trip History" />
          <Tab label="Payments" />
          <Tab label="Documents" />
          <Tab label="Notes & Activity" />
        </Tabs>
        
        <TabPanel value={tab} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                Contact Information
              </Typography>
              <Typography variant="body1">{client.email}</Typography>
              <Typography variant="body1">{client.phone}</Typography>
              <Typography variant="body1">{client.address}</Typography>
              <Typography variant="body1">{client.city}, {client.state} {client.zip_code}</Typography>
            </Grid>
          </Grid>
        </TabPanel>
        
        <TabPanel value={tab} index={1}>
          <Typography variant="body1">Trip history tab - To be implemented</Typography>
        </TabPanel>
        
        <TabPanel value={tab} index={2}>
          <Typography variant="body1">Payment history tab - To be implemented</Typography>
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
